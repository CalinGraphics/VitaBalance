/** Fundalul anteturilor de pagină: două pete teal care se mișcă lent și o grilă fină care se stinge spre dreapta-jos. */
const HeroBackdrop = () => (
  <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
    <div className="absolute -left-24 -top-32 h-80 w-80 animate-aurora rounded-full bg-accent/[0.13] blur-3xl" />
    <div className="absolute -right-16 top-10 h-64 w-64 animate-aurora-slow rounded-full bg-emerald-400/[0.07] blur-3xl" />
    <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_at_top_left,black,transparent_70%)]" />
  </div>
)

export default HeroBackdrop
