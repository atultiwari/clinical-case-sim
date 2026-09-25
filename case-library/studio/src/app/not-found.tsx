import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl rounded-md border p-4">
      <h1 className="mb-2 font-semibold">Not found</h1>
      <p>
        No such case version or page. <Link href="/">Back to the case list</Link>.
      </p>
    </div>
  );
}
