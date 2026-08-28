export function Logo({
  width = 272,
  height = 92,
  className = "",
}: {
  width?: number;
  height?: number;
  className?: string;
}) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 520 120"
      width={width}
      height={height}
      className={className}
      aria-label="NomEngine Logo"
    >
      <defs>
        <style>{`
          .nom-text {
            font-family: 'Google Sans', 'Product Sans', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 78px;
            font-weight: 500;
            letter-spacing: -2px;
          }
          .c-blue   { fill: #4285F4; }
          .c-red    { fill: #EA4335; }
          .c-yellow { fill: #FBBC05; }
          .c-green  { fill: #34A853; }
        `}</style>
      </defs>

      <text x="20" y="88" className="nom-text">
        <tspan className="c-blue">N</tspan>
        <tspan className="c-red">o</tspan>
        <tspan className="c-yellow">m</tspan>
        <tspan className="c-blue">E</tspan>
        <tspan className="c-green">n</tspan>
        <tspan className="c-red">g</tspan>
        <tspan className="c-blue">i</tspan>
        <tspan className="c-green">n</tspan>
        <tspan className="c-red">e</tspan>
      </text>
    </svg>
  );
}
