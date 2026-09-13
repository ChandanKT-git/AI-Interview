import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../lib/api";
import { Spinner } from "../components/ui";
import { ResultView } from "./Results";

export default function Share() {
  const { shareId } = useParams();
  const [iv, setIv] = useState(null);

  useEffect(() => {
    api.get(`/public/interviews/${shareId}`).then((r) => setIv(r.data)).catch(() => setIv(false));
  }, [shareId]);

  if (iv === null) return <div className="flex justify-center py-24"><Spinner className="w-7 h-7 text-primary" /></div>;
  if (iv === false)
    return <div className="text-center py-24 text-muted">This report is unavailable or the interview isn't completed.</div>;
  return <ResultView iv={iv} shared />;
}
