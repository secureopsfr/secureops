import { AuthFormSkeleton } from "../../../components/skeletons";

export default function Loading() {
  return (
    <>
      <h1 className="sr-only">Inscription</h1>
      <h2 className="sr-only">Inscription avec email</h2>
      <AuthFormSkeleton />
    </>
  );
}
