import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import api from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button, Card, Spinner, Pill, fadeUp } from "../components/ui";
import {
  Plus, Trophy, TrendingUp, Target, Award, ArrowRight, Footprints, Flame,
  Star, Crown, MessagesSquare, Layers, Lock,
} from "lucide-react";

const BADGE_ICONS = { footprints: Footprints, flame: Flame, trophy: Trophy, star: Star, crown: Crown, "messages-square": MessagesSquare, layers: Layers };

function StatCard({ label, value, suffix, icon: Icon }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="overline">{label}</span>
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div className="font-heading font-extrabold text-3xl tracking-tight">
        {value}
        {suffix && <span className="text-lg text-muted font-medium ml-0.5">{suffix}</span>}
      </div>
    </Card>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/dashboard").then((r) => setData(r.data)).catch(() => setData(false));
  }, []);

  if (data === null)
    return <div className="flex justify-center py-24"><Spinner className="w-7 h-7 text-primary" /></div>;

  const stats = data.stats || {};
  const empty = stats.total_interviews === 0;

  return (
    <div className="max-w-7xl mx-auto px-5 md:px-8 py-10">
      <motion.div {...fadeUp} className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <div className="overline mb-1">Welcome back</div>
          <h1 className="font-heading font-extrabold text-3xl sm:text-4xl tracking-tight">{user?.name}</h1>
        </div>
        <Link to="/start">
          <Button variant="primary" className="!px-5 !py-3" data-testid="start-interview-btn">
            <Plus className="w-4 h-4" /> New interview
          </Button>
        </Link>
      </motion.div>

      {empty ? (
        <motion.div {...fadeUp}>
          <Card className="p-10 md:p-16 text-center relative overflow-hidden">
            <img
              src="https://images.pexels.com/photos/6804612/pexels-photo-6804612.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
              alt="" className="absolute inset-0 w-full h-full object-cover opacity-[0.06]"
            />
            <div className="relative">
              <div className="w-14 h-14 bg-primary/10 text-primary rounded-sm flex items-center justify-center mx-auto mb-5">
                <Target className="w-7 h-7" />
              </div>
              <h2 className="font-heading font-bold text-2xl mb-2">No interviews yet</h2>
              <p className="text-muted max-w-md mx-auto mb-6">
                Run your first AI mock interview to unlock your progress dashboard, scores and badges.
              </p>
              <Link to="/start">
                <Button variant="primary" className="!px-6 !py-3" data-testid="empty-start-btn">
                  Start your first interview <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </Card>
        </motion.div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Interviews" value={stats.total_interviews} icon={Target} />
            <StatCard label="Avg Score" value={stats.avg_overall} suffix="/100" icon={TrendingUp} />
            <StatCard label="Best Score" value={stats.best_score} suffix="/100" icon={Trophy} />
            <StatCard label="Badges" value={stats.badges_earned} icon={Award} />
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-8">
            <Card className="p-6">
              <h3 className="font-heading font-bold text-lg mb-4">Skill breakdown</h3>
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={data.skill_breakdown}>
                  <PolarGrid stroke="#DEE2E6" />
                  <PolarAngleAxis dataKey="skill" tick={{ fill: "#111", fontSize: 13 }} />
                  <Radar dataKey="score" stroke="#002FA7" fill="#002FA7" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>

            <Card className="p-6">
              <h3 className="font-heading font-bold text-lg mb-4">Score trend</h3>
              {data.trend.length > 1 ? (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={data.trend} margin={{ left: -20, right: 8, top: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E9ECEF" />
                    <XAxis dataKey="index" tick={{ fill: "#6C757D", fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#6C757D", fontSize: 12 }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="overall" stroke="#002FA7" strokeWidth={2.5} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[260px] flex items-center justify-center text-sm text-muted text-center px-6">
                  Complete a few more interviews to see your improvement trend.
                </div>
              )}
            </Card>
          </div>

          {/* Badges */}
          <Card className="p-6 mb-8">
            <h3 className="font-heading font-bold text-lg mb-4">Badges</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {data.badges.map((b) => {
                const Icon = BADGE_ICONS[b.icon] || Award;
                return (
                  <div key={b.id} data-testid={`badge-${b.id}`}
                    className={`border rounded-sm p-3 text-center ${b.earned ? "border-primary bg-primary/5" : "border-line opacity-60"}`}>
                    <div className={`w-9 h-9 mx-auto rounded-sm flex items-center justify-center mb-2 ${b.earned ? "bg-primary text-white" : "bg-surface text-muted"}`}>
                      {b.earned ? <Icon className="w-4.5 h-4.5" /> : <Lock className="w-4 h-4" />}
                    </div>
                    <div className="text-xs font-medium leading-tight">{b.name}</div>
                  </div>
                );
              })}
            </div>
          </Card>
        </>
      )}

      {/* Recent */}
      {data.recent?.length > 0 && (
        <Card className="p-6">
          <h3 className="font-heading font-bold text-lg mb-4">Recent interviews</h3>
          <div className="divide-y divide-line">
            {data.recent.map((iv) => (
              <div key={iv.interview_id} className="flex items-center justify-between py-3 gap-4" data-testid={`recent-${iv.interview_id}`}>
                <div className="min-w-0">
                  <div className="font-medium truncate">{iv.pack_title || iv.role}</div>
                  <div className="text-xs text-muted flex items-center gap-2 mt-0.5">
                    <Pill className="border-line text-muted capitalize">{iv.base_difficulty}</Pill>
                    <span className="capitalize">{iv.status}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {iv.status === "completed" ? (
                    <span className="font-heading font-bold text-xl text-primary">{iv.scores?.overall}</span>
                  ) : (
                    <Pill className="border-warn/50 text-warn bg-warn/5">In progress</Pill>
                  )}
                  <Button variant="outline" className="!px-3 !py-1.5"
                    onClick={() => navigate(iv.status === "completed" ? `/results/${iv.interview_id}` : `/interview/${iv.interview_id}`)}
                    data-testid={`recent-view-${iv.interview_id}`}>
                    {iv.status === "completed" ? "View" : "Resume"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
