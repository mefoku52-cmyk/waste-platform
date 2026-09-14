import { ReactNode } from "react";

export function AppShell({
  header,
  children,
}: {
  header: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-950">
      {header}

      <div className="mx-auto w-full max-w-7xl px-3 py-3 sm:px-6 sm:py-6">
        {children}
      </div>
    </div>
  );
}
