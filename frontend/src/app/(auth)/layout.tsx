export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#1A1A2E] p-6">
      <h1 className="mb-8 text-3xl font-bold">
        Gully<span className="text-[#E94560]">Dream11</span>
      </h1>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
