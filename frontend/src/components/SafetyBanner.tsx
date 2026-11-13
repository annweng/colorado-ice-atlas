export function SafetyBanner() {
  return (
    <div className="border-b border-amber-500/30 bg-amber-950/70 px-4 py-2 text-[12px] leading-snug text-amber-100 md:text-[13px]">
      Modeled ice thickness is not a field measurement and does not mean ice is safe to walk, skate, fish, or drive on.
      Thickness varies across a lake. Local conditions can differ substantially from these estimates. Verify on site.
    </div>
  );
}
