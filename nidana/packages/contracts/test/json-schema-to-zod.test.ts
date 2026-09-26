import { describe, expect, it } from "vitest";
import {
  UnsupportedSchemaError,
  generateZodModule,
  pascalCase,
} from "../scripts/json-schema-to-zod.ts";

const options = { rootName: "Root", header: "// test" };

function generate(root: Record<string, unknown>): string {
  return generateZodModule(root, options);
}

function failure(root: Record<string, unknown>): string {
  try {
    generate(root);
  } catch (error) {
    expect(error).toBeInstanceOf(UnsupportedSchemaError);
    return (error as Error).message;
  }
  throw new Error("expected the generator to refuse the schema");
}

describe("generateZodModule", () => {
  it("emits definitions before the definitions that use them eagerly", () => {
    const source = generate({
      type: "object",
      properties: { a: { $ref: "#/$defs/b_or_null" } },
      $defs: {
        b_or_null: { oneOf: [{ type: "null" }, { $ref: "#/$defs/b" }] },
        b: { type: "string" },
      },
    });
    expect(source.indexOf("export const B =")).toBeLessThan(
      source.indexOf("export const BOrNull ="),
    );
    expect(source).toContain("export const BOrNull = B.nullable();");
    expect(source).toContain("get a() { return BOrNull.optional(); }");
  });

  it("emits unions, literal enums, numbers and bounded arrays", () => {
    const source = generate({
      type: "object",
      required: ["a", "b", "c", "d"],
      properties: {
        a: { oneOf: [{ type: "string" }, { type: "integer" }] },
        b: { enum: [1, 2] },
        c: { type: "number", minimum: 0 },
        d: { type: "array", minItems: 1, maxItems: 3 },
        e: { enum: [true] },
      },
    });
    expect(source).toContain("a: z.union([z.string(), z.number().int()])");
    expect(source).toContain("b: z.union([z.literal(1), z.literal(2)])");
    expect(source).toContain("c: z.number().min(0)");
    expect(source).toContain("d: z.array(z.unknown()).min(1).max(3)");
    expect(source).toContain("e: z.literal(true).optional()");
  });

  it("describes if/then rules it cannot put into words generically", () => {
    const source = generate({
      type: "object",
      if: { properties: { a: { type: "string" } } },
      then: { required: ["b"], properties: { b: { type: "string" } } },
      properties: { a: { type: "string" } },
    });
    expect(source).toContain("under the schema's if/then rule");
  });

  it.each([
    [{ type: "string", maxLength: 3 }, 'unsupported keyword "maxLength"'],
    [{ type: "string", format: "email" }, 'unsupported format "email"'],
    [{ type: "widget" }, 'unknown type "widget"'],
    [{ type: ["string", "number"] }, "only one non-null type"],
    [{ minimum: 1 }, "needs a type"],
    [{ $ref: "#/$defs/missing" }, "unresolved $ref"],
    [
      { $ref: "#/$defs/a", type: "string" },
      "$ref cannot have sibling keywords",
    ],
    [{ oneOf: [{ type: "string" }] }, "at least two branches"],
    [
      { oneOf: [{ type: "string" }, { type: "string", pattern: "x" }] },
      "different JSON types",
    ],
    [{ oneOf: [{ type: "string" }, {}] }, "different JSON types"],
    [
      { oneOf: [{ type: "null" }, { type: "string" }], type: "string" },
      "oneOf cannot have sibling",
    ],
    [{ enum: [] }, "at least one value"],
    [
      { type: "array", prefixItems: [{ type: "string" }] },
      "fixed-length tuple",
    ],
    [{ type: "array", minItems: "1" }, "minItems must be a number"],
    [
      { type: "object", required: ["a"] },
      'required "a" has no property schema',
    ],
    [
      { type: "object", required: ["a"], properties: { a: {} } },
      "a required property needs a schema",
    ],
    [{ type: "object", required: "a" }, "required must be a list of names"],
    [
      { type: "object", additionalProperties: { type: "string" } },
      "additionalProperties is supported only as false",
    ],
    [{ type: "object", properties: [] }, "expected a schema object"],
  ])("refuses %j", (schema, detail) => {
    expect(failure(schema as Record<string, unknown>)).toContain(detail);
  });

  it("refuses definitions that need each other at load time", () => {
    const message = failure({
      $defs: {
        a: { type: "array", items: { $ref: "#/$defs/b" } },
        b: { type: "array", items: { $ref: "#/$defs/a" } },
      },
      type: "string",
    });
    expect(message).toContain("refer to each other outside objects");
  });

  it("refuses definition names that collide", () => {
    const message = failure({
      $defs: { a_b: { type: "string" }, aB: { type: "string" } },
      type: "string",
    });
    expect(message).toContain("collide");
  });

  it("points at the failing location", () => {
    const message = failure({
      type: "object",
      properties: { a: { type: "array", items: { not: {} } } },
    });
    expect(message).toBe('#/properties/a/items: unsupported keyword "not"');
  });
});

describe("pascalCase", () => {
  it("joins snake case words", () => {
    expect(pascalCase("ledger_row")).toBe("LedgerRow");
    expect(pascalCase("condition_or_null")).toBe("ConditionOrNull");
  });
});
