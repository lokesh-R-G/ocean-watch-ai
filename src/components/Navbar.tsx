import { Waves, LayoutDashboard, FileText, Bell } from "lucide-react";

const navLinks = [
  { label: "DASHBOARD", icon: LayoutDashboard },
  { label: "REPORTS", icon: FileText },
  { label: "ALERTS", icon: Bell },
];

const Navbar = () => {
  return (
    <nav className="fixed top-0 left-0 right-0 z-[1000] glass-card rounded-none border-x-0 border-t-0">
      <div className="flex items-center justify-between px-6 py-3">
        <div className="flex items-center gap-3">
          <Waves className="h-6 w-6 text-primary animate-breathe" />
          <h1 className="text-sm font-semibold tracking-widest uppercase text-foreground">
            AI Ocean Plastic Monitoring
          </h1>
        </div>
        <div className="flex items-center gap-1">
          {navLinks.map((link) => (
            <button
              key={link.label}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium tracking-wider text-muted-foreground hover:text-primary hover:bg-secondary/50 transition-all duration-200"
            >
              <link.icon className="h-3.5 w-3.5" />
              {link.label}
            </button>
          ))}
          <div className="ml-3 relative">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-heat-high" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
