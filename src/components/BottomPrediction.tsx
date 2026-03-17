import { MapPin, ArrowRight, Clock } from "lucide-react";

const BottomPrediction = () => {
  return (
    <div className="glass-card glow-border px-6 py-4 animate-fade-in">
      <div className="flex items-center gap-3 mb-3">
        <Clock className="h-4 w-4 text-primary" />
        <h2 className="text-xs font-semibold tracking-widest uppercase text-primary">
          Prediction (120 Minutes)
        </h2>
      </div>

      <div className="flex items-center justify-between gap-6 flex-wrap">
        {/* Current Location */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-heat-low/20 flex items-center justify-center">
            <MapPin className="h-5 w-5 text-heat-low" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Current Location
            </p>
            <p className="font-mono text-sm text-foreground">
              <span className="text-primary">15.4231°N</span>,{" "}
              <span className="text-primary">88.7654°E</span>
            </p>
          </div>
        </div>

        {/* Arrow */}
        <div className="flex items-center gap-2">
          <div className="h-px w-12 bg-gradient-to-r from-heat-low to-heat-high" />
          <ArrowRight className="h-5 w-5 text-heat-medium animate-breathe" />
          <div className="h-px w-12 bg-gradient-to-r from-heat-medium to-heat-high" />
        </div>

        {/* Predicted Location */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-heat-high/20 flex items-center justify-center">
            <MapPin className="h-5 w-5 text-heat-high" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Predicted Location
            </p>
            <p className="font-mono text-sm text-foreground">
              <span className="text-heat-high">15.4897°N</span>,{" "}
              <span className="text-heat-high">88.8321°E</span>
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-6 ml-auto">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Distance
            </p>
            <p className="font-mono text-sm text-foreground">
              9.2 <span className="text-muted-foreground">km</span>
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Speed
            </p>
            <p className="font-mono text-sm text-foreground">
              4.6 <span className="text-muted-foreground">km/h</span>
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
              Confidence
            </p>
            <p className="font-mono text-sm text-primary">87%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BottomPrediction;
