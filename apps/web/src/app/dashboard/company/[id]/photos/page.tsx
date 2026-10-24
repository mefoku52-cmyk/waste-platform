export default function CompanyFotkyPage() {
  return (
    <div>
      <div className="mb-8 overflow-hidden rounded-2xl border border-[rgba(201,168,76,0.25)] relative h-48 flex items-center justify-center">
        <img 
          src="https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=1200&q=80" 
          alt="Fotky" 
          className="absolute inset-0 h-full w-full object-cover opacity-40" 
        />
        <h1 className="relative z-10 font-serif text-4xl text-[#c9a84c]">
          Fotky
        </h1>
      </div>
      
      <div className="rounded-xl border p-6 bg-[#0b0b0b]" style={{ borderColor: "rgba(201,168,76,0.25)" }}>
        <p className="text-sm text-[#9a8f7c]">
          Táto sekcia je pripravená. Čoskoro tu pribudne správa pre fotky.
        </p>
      </div>
    </div>
  );
}
