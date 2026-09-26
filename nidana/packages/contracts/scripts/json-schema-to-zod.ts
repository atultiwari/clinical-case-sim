/**
 * Turns the Case Library's bundle schema (JSON Schema 2020-12) into a TypeScript module of Zod
 * validators and inferred types.
 *
 * It supports exactly the keywords the schema uses and throws on anything else, so a schema
 * change that needs a new keyword fails loudly here instead of being silently ignored.
 * `oneOf` becomes a union only when its branches have different JSON types, where "exactly one"
 * and "at least one" mean the same thing.
 */

type Schema = { readonly [keyword: string]: unknown };

const ANNOTATIONS = new Set([
  "$schema",
  "$id",
  "title",
  "description",
  "$comment",
]);
const KEYWORDS = new Set([
  "$ref",
  "$defs",
  "oneOf",
  "const",
  "enum",
  "type",
  "format",
  "pattern",
  "minimum",
  "items",
  "prefixItems",
  "minItems",
  "maxItems",
  "properties",
  "required",
  "additionalProperties",
  "minProperties",
  "maxProperties",
  "dependentRequired",
  "if",
  "then",
]);
const FORMATS: Readonly<Record<string, string>> = { date: "z.iso.date()" };
const JSON_TYPES = [
  "null",
  "boolean",
  "object",
  "array",
  "number",
  "integer",
  "string",
] as const;
type JsonType = (typeof JSON_TYPES)[number];

export class UnsupportedSchemaError extends Error {
  constructor(pointer: string, detail: string) {
    super(`${pointer || "#"}: ${detail}`);
    this.name = "UnsupportedSchemaError";
  }
}

interface Helper {
  readonly name: string;
  readonly expr: string;
}

interface Context {
  readonly root: Schema;
  readonly defNames: ReadonlyMap<string, string>;
  /** Hoisted sub-schemas (if/then) for the definition being emitted. */
  readonly helpers: Helper[];
  readonly owner: string;
  /** Definitions the current expression refers to. */
  readonly refs: Set<string>;
  /** Definitions the owner needs when the module loads (outside getters). */
  readonly eager: Set<string>;
  /** True inside a getter, where references are resolved only when parsing. */
  readonly lazy: boolean;
}

export interface GenerateOptions {
  /** Name of the exported root validator and type, for example `CaseBundle`. */
  readonly rootName: string;
  /** First lines of the module, usually a "generated, do not edit" comment. */
  readonly header: string;
}

export function pascalCase(name: string): string {
  return name
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
}

function isSchema(value: unknown): value is Schema {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asSchema(value: unknown, pointer: string): Schema {
  if (!isSchema(value))
    throw new UnsupportedSchemaError(pointer, "expected a schema object");
  return value;
}

function checkKeywords(schema: Schema, pointer: string): void {
  for (const keyword of Object.keys(schema)) {
    if (!KEYWORDS.has(keyword) && !ANNOTATIONS.has(keyword)) {
      throw new UnsupportedSchemaError(
        pointer,
        `unsupported keyword "${keyword}"`,
      );
    }
  }
}

function refName(ref: unknown, ctx: Context, pointer: string): string {
  const match =
    typeof ref === "string" ? /^#\/\$defs\/([A-Za-z0-9_]+)$/.exec(ref) : null;
  const name =
    match?.[1] === undefined ? undefined : ctx.defNames.get(match[1]);
  if (name === undefined)
    throw new UnsupportedSchemaError(pointer, `unresolved $ref ${String(ref)}`);
  ctx.refs.add(name);
  if (!ctx.lazy) ctx.eager.add(name);
  return name;
}

function declaredTypes(schema: Schema, pointer: string): JsonType[] {
  const raw = schema.type;
  if (raw === undefined) return [];
  const list = Array.isArray(raw) ? raw : [raw];
  return list.map((type) => {
    if (!JSON_TYPES.includes(type as JsonType)) {
      throw new UnsupportedSchemaError(
        pointer,
        `unknown type ${JSON.stringify(type)}`,
      );
    }
    return type as JsonType;
  });
}

/** The JSON types a schema can match, following $ref; `undefined` means any type. */
function possibleTypes(
  schema: Schema,
  ctx: Context,
  pointer: string,
): Set<string> | undefined {
  if (schema.$ref !== undefined) {
    const key = String(schema.$ref).replace("#/$defs/", "");
    const defs = asSchema(ctx.root.$defs, "#/$defs");
    return possibleTypes(asSchema(defs[key], `#/$defs/${key}`), ctx, pointer);
  }
  if (schema.const !== undefined) return new Set([jsonTypeOf(schema.const)]);
  if (Array.isArray(schema.oneOf)) {
    const all = new Set<string>();
    for (const [i, branch] of schema.oneOf.entries()) {
      const types = possibleTypes(
        asSchema(branch, `${pointer}/oneOf/${i}`),
        ctx,
        pointer,
      );
      if (types === undefined) return undefined;
      types.forEach((t) => all.add(t));
    }
    return all;
  }
  const types = declaredTypes(schema, pointer);
  if (types.length > 0)
    return new Set(types.map((t) => (t === "integer" ? "number" : t)));
  if (schema.properties !== undefined || schema.required !== undefined)
    return new Set(["object"]);
  return undefined;
}

function jsonTypeOf(value: unknown): string {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

function emitOneOf(branches: unknown, ctx: Context, pointer: string): string {
  if (!Array.isArray(branches) || branches.length < 2) {
    throw new UnsupportedSchemaError(
      pointer,
      "oneOf needs at least two branches",
    );
  }
  const schemas = branches.map((b, i) => asSchema(b, `${pointer}/oneOf/${i}`));
  const seen = new Set<string>();
  for (const [i, branch] of schemas.entries()) {
    const types = possibleTypes(branch, ctx, `${pointer}/oneOf/${i}`);
    if (types === undefined || [...types].some((t) => seen.has(t))) {
      throw new UnsupportedSchemaError(
        pointer,
        "oneOf branches must have different JSON types",
      );
    }
    types.forEach((t) => seen.add(t));
  }
  const isNull = (s: Schema) =>
    s.type === "null" && Object.keys(s).length === 1;
  const others = schemas.filter((s) => !isNull(s));
  const hasNull = others.length < schemas.length;
  const exprs = others.map((s) =>
    emit(s, ctx, `${pointer}/oneOf/${schemas.indexOf(s)}`),
  );
  const union =
    exprs.length === 1
      ? (exprs[0] as string)
      : `z.union([${exprs.join(", ")}])`;
  return hasNull ? `${union}.nullable()` : union;
}

function emitEnum(values: unknown, pointer: string): string {
  if (!Array.isArray(values) || values.length === 0) {
    throw new UnsupportedSchemaError(pointer, "enum needs at least one value");
  }
  if (values.every((v) => typeof v === "string"))
    return `z.enum(${JSON.stringify(values)})`;
  const literals = values.map((v) => `z.literal(${JSON.stringify(v)})`);
  return literals.length === 1
    ? (literals[0] as string)
    : `z.union([${literals.join(", ")}])`;
}

function numberOrThrow(
  value: unknown,
  pointer: string,
  keyword: string,
): number {
  if (typeof value !== "number")
    throw new UnsupportedSchemaError(pointer, `${keyword} must be a number`);
  return value;
}

function emitString(schema: Schema, pointer: string): string {
  let expr = "z.string()";
  if (schema.format !== undefined) {
    const format = FORMATS[String(schema.format)];
    if (format === undefined) {
      throw new UnsupportedSchemaError(
        pointer,
        `unsupported format "${String(schema.format)}"`,
      );
    }
    expr = format;
  }
  if (schema.pattern !== undefined) {
    expr += `.regex(new RegExp(${JSON.stringify(schema.pattern)}))`;
  }
  return expr;
}

function emitNumber(schema: Schema, integer: boolean, pointer: string): string {
  const base = integer ? "z.number().int()" : "z.number()";
  if (schema.minimum === undefined) return base;
  return `${base}.min(${numberOrThrow(schema.minimum, pointer, "minimum")})`;
}

function emitArray(schema: Schema, ctx: Context, pointer: string): string {
  const min =
    schema.minItems === undefined
      ? undefined
      : numberOrThrow(schema.minItems, pointer, "minItems");
  const max =
    schema.maxItems === undefined
      ? undefined
      : numberOrThrow(schema.maxItems, pointer, "maxItems");
  if (schema.prefixItems !== undefined) {
    const prefix = schema.prefixItems;
    if (
      !Array.isArray(prefix) ||
      schema.items !== undefined ||
      min !== prefix.length ||
      max !== prefix.length
    ) {
      throw new UnsupportedSchemaError(
        pointer,
        "prefixItems is supported only as a fixed-length tuple",
      );
    }
    const items = prefix.map((p, i) =>
      emit(
        asSchema(p, `${pointer}/prefixItems/${i}`),
        ctx,
        `${pointer}/prefixItems/${i}`,
      ),
    );
    return `z.tuple([${items.join(", ")}])`;
  }
  const items =
    schema.items === undefined
      ? "z.unknown()"
      : emit(
          asSchema(schema.items, `${pointer}/items`),
          ctx,
          `${pointer}/items`,
        );
  let expr = `z.array(${items})`;
  if (min !== undefined) expr += `.min(${min})`;
  if (max !== undefined) expr += `.max(${max})`;
  return expr;
}

function stringList(
  value: unknown,
  pointer: string,
  keyword: string,
): string[] {
  if (!Array.isArray(value) || !value.every((v) => typeof v === "string")) {
    throw new UnsupportedSchemaError(
      pointer,
      `${keyword} must be a list of names`,
    );
  }
  return value;
}

function emitShape(schema: Schema, ctx: Context, pointer: string): string {
  const properties =
    schema.properties === undefined
      ? {}
      : asSchema(schema.properties, `${pointer}/properties`);
  const required = new Set(
    schema.required === undefined
      ? []
      : stringList(schema.required, pointer, "required"),
  );
  for (const name of required) {
    if (!(name in properties))
      throw new UnsupportedSchemaError(
        pointer,
        `required "${name}" has no property schema`,
      );
  }
  const entries = Object.entries(properties).map(([name, value]) => {
    const propPointer = `${pointer}/properties/${name}`;
    const prop = asSchema(value, propPointer);
    const unconstrained = Object.keys(prop).every((k) => ANNOTATIONS.has(k));
    if (unconstrained && required.has(name)) {
      throw new UnsupportedSchemaError(
        propPointer,
        "a required property needs a schema",
      );
    }
    // Getters defer references to other definitions, which allows recursion and any order.
    const propCtx: Context = { ...ctx, refs: new Set(), lazy: true };
    const expr =
      emit(prop, propCtx, propPointer) +
      (required.has(name) ? "" : ".optional()");
    const key = /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(name)
      ? name
      : JSON.stringify(name);
    return propCtx.refs.size > 0
      ? `get ${key}() { return ${expr}; }`
      : `${key}: ${expr}`;
  });
  return `{ ${entries.join(", ")} }`;
}

function describeIf(schema: Schema): string {
  const properties = isSchema(schema.properties)
    ? Object.entries(schema.properties)
    : [];
  const parts = properties.flatMap(([name, value]) =>
    isSchema(value) && value.const !== undefined
      ? [`${name} is ${JSON.stringify(value.const)}`]
      : [],
  );
  const describable =
    parts.length > 0 &&
    parts.length === properties.length &&
    Object.keys(schema).length === 1;
  return describable
    ? `when ${parts.join(" and ")}`
    : "under the schema's if/then rule";
}

/** Emits a sub-schema as a module-level constant, built once when the module loads. */
function hoist(
  schema: Schema,
  ctx: Context,
  suffix: string,
  pointer: string,
): string {
  const expr = emit(schema, { ...ctx, refs: new Set(), lazy: false }, pointer);
  const name = `${ctx.owner}${suffix}${ctx.helpers.length + 1}`;
  ctx.helpers.push({ name, expr });
  return name;
}

function objectChecks(schema: Schema, ctx: Context, pointer: string): string[] {
  const checks: string[] = [];
  const min =
    schema.minProperties === undefined
      ? undefined
      : numberOrThrow(schema.minProperties, pointer, "minProperties");
  const max =
    schema.maxProperties === undefined
      ? undefined
      : numberOrThrow(schema.maxProperties, pointer, "maxProperties");
  if (min !== undefined || max !== undefined) {
    const tests = [
      min === undefined ? null : `count < ${min}`,
      max === undefined ? null : `count > ${max}`,
    ].filter(Boolean);
    const range = `${min ?? 0} to ${max ?? "any number of"}`;
    checks.push(
      `const count = Object.keys(value).length;
       if (${tests.join(" || ")}) {
         ctx.addIssue({ code: "custom", message: \`expected ${range} properties, found \${count}\` });
       }`,
    );
  }
  if (schema.dependentRequired !== undefined) {
    for (const [name, deps] of Object.entries(
      asSchema(schema.dependentRequired, `${pointer}/dependentRequired`),
    )) {
      for (const dep of stringList(
        deps,
        `${pointer}/dependentRequired/${name}`,
        "dependentRequired",
      )) {
        checks.push(
          `if (${JSON.stringify(name)} in value && !(${JSON.stringify(dep)} in value)) {
             ctx.addIssue({ code: "custom", path: [${JSON.stringify(dep)}], message: ${JSON.stringify(`required when "${name}" is present`)} });
           }`,
        );
      }
    }
  }
  if (schema.if !== undefined || schema.then !== undefined) {
    const ifSchema = asSchema(schema.if, `${pointer}/if`);
    const thenSchema = asSchema(schema.then, `${pointer}/then`);
    const ifName = hoist(ifSchema, ctx, "If", `${pointer}/if`);
    const thenName = hoist(thenSchema, ctx, "Then", `${pointer}/then`);
    checks.push(
      `if (${ifName}.safeParse(value).success) {
         const result = ${thenName}.safeParse(value);
         for (const issue of result.error?.issues ?? []) {
           ctx.addIssue({ code: "custom", path: issue.path, message: \`\${issue.message} (${describeIf(ifSchema)})\` });
         }
       }`,
    );
  }
  return checks;
}

function emitObject(schema: Schema, ctx: Context, pointer: string): string {
  const strict = schema.additionalProperties === false;
  if (schema.additionalProperties !== undefined && !strict) {
    throw new UnsupportedSchemaError(
      pointer,
      "additionalProperties is supported only as false",
    );
  }
  const hasShape =
    schema.properties !== undefined || schema.required !== undefined;
  const base =
    !hasShape && !strict
      ? "z.record(z.string(), z.unknown())"
      : `${strict ? "z.strictObject" : "z.looseObject"}(${emitShape(schema, ctx, pointer)})`;
  const checks = objectChecks(schema, ctx, pointer);
  if (checks.length === 0) return base;
  return `${base}.superRefine((value, ctx) => { ${checks.join("\n")} })`;
}

function emitTyped(
  type: JsonType,
  schema: Schema,
  ctx: Context,
  pointer: string,
): string {
  switch (type) {
    case "string":
      return emitString(schema, pointer);
    case "integer":
      return emitNumber(schema, true, pointer);
    case "number":
      return emitNumber(schema, false, pointer);
    case "boolean":
      return "z.boolean()";
    case "array":
      return emitArray(schema, ctx, pointer);
    case "object":
      return emitObject(schema, ctx, pointer);
    case "null":
      return "z.null()";
  }
}

/** One schema as a Zod expression. */
function emit(schema: Schema, ctx: Context, pointer: string): string {
  checkKeywords(schema, pointer);
  const constraints = Object.keys(schema).filter((k) => !ANNOTATIONS.has(k));
  if (schema.$ref !== undefined) {
    if (constraints.length > 1)
      throw new UnsupportedSchemaError(
        pointer,
        "$ref cannot have sibling keywords",
      );
    return refName(schema.$ref, ctx, pointer);
  }
  if (schema.oneOf !== undefined) {
    if (constraints.length > 1)
      throw new UnsupportedSchemaError(
        pointer,
        "oneOf cannot have sibling keywords",
      );
    return emitOneOf(schema.oneOf, ctx, pointer);
  }
  if (schema.const !== undefined)
    return `z.literal(${JSON.stringify(schema.const)})`;
  if (schema.enum !== undefined) return emitEnum(schema.enum, pointer);

  let types = declaredTypes(schema, pointer);
  if (types.length === 0) {
    if (constraints.length === 0) return "z.unknown()";
    if (schema.properties !== undefined || schema.required !== undefined)
      types = ["object"];
    else
      throw new UnsupportedSchemaError(
        pointer,
        "a schema with constraints needs a type",
      );
  }
  const nullable = types.includes("null");
  const others = types.filter((t) => t !== "null");
  if (others.length === 0) return "z.null()";
  if (others.length > 1)
    throw new UnsupportedSchemaError(
      pointer,
      "only one non-null type is supported",
    );
  const expr = emitTyped(others[0] as JsonType, schema, ctx, pointer);
  return nullable ? `${expr}.nullable()` : expr;
}

function orderDefinitions(
  eager: ReadonlyMap<string, ReadonlySet<string>>,
): string[] {
  const ordered: string[] = [];
  const visiting = new Set<string>();
  const visit = (name: string): void => {
    if (ordered.includes(name)) return;
    if (visiting.has(name)) {
      throw new UnsupportedSchemaError(
        "#/$defs",
        `definitions refer to each other outside objects: ${name}`,
      );
    }
    visiting.add(name);
    [...(eager.get(name) ?? [])].filter((dep) => dep !== name).forEach(visit);
    visiting.delete(name);
    ordered.push(name);
  };
  [...eager.keys()].forEach(visit);
  return ordered;
}

function docComment(schema: Schema): string {
  return typeof schema.description === "string"
    ? `/** ${schema.description.replaceAll("*/", "* /")} */\n`
    : "";
}

/** The whole module, unformatted. */
export function generateZodModule(
  root: Schema,
  options: GenerateOptions,
): string {
  checkKeywords(root, "#");
  const defs = root.$defs === undefined ? {} : asSchema(root.$defs, "#/$defs");
  const defNames = new Map(
    Object.keys(defs).map((key) => [key, pascalCase(key)]),
  );
  if (
    defNames.size !== new Set(defNames.values()).size ||
    [...defNames.values()].includes(options.rootName)
  ) {
    throw new UnsupportedSchemaError(
      "#/$defs",
      "definition names collide after conversion",
    );
  }

  const blocks = new Map<string, string>();
  const eager = new Map<string, Set<string>>();
  const render = (name: string, schema: Schema, pointer: string): void => {
    const helpers: Helper[] = [];
    const needs = new Set<string>();
    const ctx: Context = {
      root,
      defNames,
      helpers,
      owner: name,
      refs: new Set(),
      eager: needs,
      lazy: false,
    };
    const expr = emit(schema, ctx, pointer);
    const hoisted = helpers
      .map((h) => `const ${h.name} = ${h.expr};\n`)
      .join("");
    blocks.set(
      name,
      `${hoisted}${docComment(schema)}export const ${name} = ${expr};\nexport type ${name} = z.infer<typeof ${name}>;\n`,
    );
    eager.set(name, needs);
  };
  for (const [key, name] of defNames)
    render(name, asSchema(defs[key], `#/$defs/${key}`), `#/$defs/${key}`);
  const rootSchema = Object.fromEntries(
    Object.entries(root).filter(([k]) => k !== "$defs"),
  );
  render(options.rootName, rootSchema, "#");

  const order = orderDefinitions(eager);
  return `${options.header}\nimport { z } from "zod";\n\n${order.map((name) => blocks.get(name)).join("\n")}`;
}
