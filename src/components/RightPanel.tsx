import { Wind, Navigation, Waves } from "lucide-react";

const RightPanel = () => {
  return (
    <div className="glass-card glow-border p-5 w-64 flex flex-col gap-5 animate-fade-in">
      <h2 className="text-xs font-semibold tracking-widest uppercase text-primary">
        Wind & Ocean Data
      </h2>

      {/* Wind Direction */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Wind className="h-4 w-4 text-primary" />
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Wind Direction
          </span>
        </div>
        <div className="flex items-center justify-between">
          <Navigation
            className="h-10 w-10 text-primary animate-breathe"
            style={{ transform: "rotate(135deg)" }}
          />
          <div className="text-right">
            <p className="text-2xl font-semibold font-mono text-foreground">
              SE
            </p>
            <p className="text-[10px] text-muted-foreground font-mono">
              135°
            </p>
          </div>
        </div>
      </div>

      {/* Wind Speed */}
      <div className="glass-card p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Wind className="h-4 w-4 text-primary" />
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Wind Speed
          </span>
        </div>
        <p className="text-3xl font-semibold font-mono text-foreground">
          12 <span className="text-sm text-muted-foreground">knots</span>
        </p>
        <div className="w-full h-1.5 rounded-full bg-secondary overflow-hidden">
          <div
            className="h-full rounded-full bg-primary"
            style={{ width: "48%" }}
          />
        </div>
      </div>

      {/* Ocean Current */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Waves className="h-4 w-4 text-primary" />
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
            Ocean Current
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <Waves
                key={i}
                className="h-6 w-6 text-primary"
                style={{
                  opacity: 0.4 + i * 0.3,
                  animationDelay: `${i * 0.3}s`,
                }}
              />
            ))}
          </div>
          <div className="text-right">
            <p className="text-lg font-semibold font-mono text-foreground">
              0.8 <span className="text-xs text-muted-foreground">m/s</span>
            </p>
            <p className="text-[10px] text-muted-foreground font-mono">
              NE Direction
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RightPanel;
