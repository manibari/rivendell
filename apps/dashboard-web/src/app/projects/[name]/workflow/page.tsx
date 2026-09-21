import { redirect } from "next/navigation";

// Default landing: the UI Feature flow. Users navigate to /backend, /slide,
// /maintenance via the inline tab nav rendered by the [flow] sub-route.
export default async function WorkflowIndex({
  params,
}: {
  params: Promise<{ name: string }>;
}) {
  const { name } = await params;
  redirect(`/projects/${name}/workflow/ui`);
}
