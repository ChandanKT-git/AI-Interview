import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button, Card } from "../components/ui";
import { useAuth } from "../context/AuthContext";
import { Mic, Brain, BarChart3, ShieldCheck, ArrowRight, Sparkles, Volume2, Target } from "lucide-react";

const features = [
  { icon: Brain, title: "Adaptive AI questions", desc: "Role-specific questions that get harder or easier based on how you perform." },
  { icon: Volume2, title: "Voice interface", desc: "Questions are read aloud and you can answer by speaking — just like the real thing." },
  { icon: Target, title: "Structured feedback", desc: "Scores for communication, technical accuracy and confidence with concrete tips." },
  { icon: BarChart3, title: "Progress dashboard", desc: "Track improvement over time, earn badges and see your weakest areas." },
];

export default function Landing() {
  const { user } = useAuth();
  const cta = user ? "/dashboard" : "/auth?mode=register";

  return (
    <div className="grain">
      {/* Hero */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 pt-16 md:pt-24 pb-16 grid lg:grid-cols-2 gap-12 items-center">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="inline-flex items-center gap-2 border border-line rounded-sm px-3 py-1 mb-6">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-medium text-muted">AI-driven mock interviews</span>
          </div>
          <h1 className="font-heading font-extrabold tracking-tight text-4xl sm:text-5xl lg:text-6xl leading-[1.05]">
            Practice interviews that <span className="text-primary">talk back.</span>
          </h1>
          <p className="mt-6 text-lg text-muted max-w-xl leading-relaxed">
            Rehearse real, role-specific interviews with an AI coach. Answer by voice or text and get
            instant, structured feedback on clarity, technical depth and confidence.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to={cta}>
              <Button variant="primary" className="!px-6 !py-3 text-base" data-testid="hero-cta-btn">
                Start practicing <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/auth">
              <Button variant="outline" className="!px-6 !py-3 text-base" data-testid="hero-login-btn">
                I have an account
              </Button>
            </Link>
          </div>
          <div className="mt-8 flex items-center gap-6 text-sm text-muted">
            <span className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-success" /> No credit card</span>
            <span className="flex items-center gap-2"><Mic className="w-4 h-4 text-primary" /> Voice ready</span>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5, delay: 0.1 }} className="relative">
          <div className="relative rounded-sm overflow-hidden border border-line">
            <img
              src="https://images.pexels.com/photos/7643739/pexels-photo-7643739.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
              alt="Professional interview in progress"
              className="w-full h-[440px] object-cover"
            />
            <div className="absolute bottom-4 left-4 right-4 bg-white/85 backdrop-blur-md border border-line rounded-sm p-4">
              <div className="overline mb-1">Live evaluation</div>
              <div className="flex items-end justify-between gap-4">
                <div>
                  <div className="text-sm font-medium">Backend Developer · Medium</div>
                  <div className="text-xs text-muted">"How would you design a rate limiter?"</div>
                </div>
                <div className="font-heading font-bold text-3xl text-primary">82</div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="border-t border-line bg-surface/60">
        <div className="max-w-7xl mx-auto px-5 md:px-8 py-16 md:py-20">
          <div className="overline mb-3">Why InterviewCoach</div>
          <h2 className="font-heading font-bold tracking-tight text-3xl sm:text-4xl max-w-2xl">
            Everything you need to walk in prepared.
          </h2>
          <div className="mt-10 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map((f, i) => (
              <motion.div key={f.title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.05 }}>
                <Card className="p-6 h-full" hover>
                  <div className="w-10 h-10 bg-primary/10 text-primary rounded-sm flex items-center justify-center mb-4">
                    <f.icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-heading font-bold text-lg mb-1.5">{f.title}</h3>
                  <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-7xl mx-auto px-5 md:px-8 py-20">
        <Card className="p-10 md:p-14 text-center bg-primary text-white border-primary">
          <h2 className="font-heading font-extrabold text-3xl sm:text-4xl tracking-tight">Ready for your next interview?</h2>
          <p className="mt-4 text-white/80 max-w-xl mx-auto">Run a free mock interview right now and see exactly where you stand.</p>
          <Link to={cta}>
            <Button variant="dark" className="!bg-white !text-primary hover:!bg-surface mt-8 !px-7 !py-3 text-base" data-testid="bottom-cta-btn">
              Begin your first interview <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </Card>
      </section>
    </div>
  );
}
