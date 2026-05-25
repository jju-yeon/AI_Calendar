import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

/*global google*/

const CLIENT_ID =
  "176306222059-571sa9nd4ele6ugemmjn8h9rvrnm13ej.apps.googleusercontent.com";
const SCOPE = "https://www.googleapis.com/auth/calendar.events";

function waitForOAuth2(timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    const start = Date.now();
    const tick = () => {
      if (window.google?.accounts?.oauth2) return resolve(true);
      if (Date.now() - start > timeoutMs)
        return reject(new Error("Google OAuth 로딩 타임아웃"));
      setTimeout(tick, 100);
    };
    tick();
  });
}

export default function ConnectCalendarPage() {
  const navigate = useNavigate();
  const tokenClientRef = useRef(null);

  const [phase, setPhase] = useState("idle"); // idle | requesting | error
  const [status, setStatus] = useState("Google 캘린더 연결을 시작하세요.");
  const [error, setError] = useState("");

  const connect = async () => {
    setPhase("requesting");
    setStatus("권한 요청 중...");
    setError("");

    try {
      await waitForOAuth2(8000);

      if (!tokenClientRef.current) {
        tokenClientRef.current = google.accounts.oauth2.initTokenClient({
          client_id: CLIENT_ID,
          scope: SCOPE,
          callback: (resp) => {
            if (!resp?.access_token) {
              setPhase("error");
              setError("권한 승인 실패(팝업 차단/테스터 설정/콘솔 에러 확인)");
              setStatus("실패");
              return;
            }

            sessionStorage.setItem("google_access_token", resp.access_token);
            setStatus("연결 완료 → 캘린더로 이동");
            navigate("/calendar", { replace: true });
          },
        });
      }

      // ✅ 반드시 사용자 클릭에서 호출되어야 팝업 차단이 덜함
      tokenClientRef.current.requestAccessToken({ prompt: "consent" });
    } catch (e) {
      setPhase("error");
      setError(String(e?.message ?? e));
      setStatus("실패");
    }
  };

  // 이미 토큰 있으면 바로 이동(선택)
  useEffect(() => {
    const t = sessionStorage.getItem("google_access_token");
    if (t) navigate("/calendar", { replace: true });
  }, [navigate]);

  const retry = () => {
    sessionStorage.removeItem("google_access_token");
    setPhase("idle");
    setStatus("Google 캘린더 연결을 시작하세요.");
    setError("");
  };

  return (
    <div
      style={{
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        gap: 12,
        justifyContent: "center",
        alignItems: "center",
        padding: 24,
      }}
    >
      <h2 style={{ margin: 0 }}>캘린더 연결</h2>
      
        <script src="https://accounts.google.com/gsi/client" async defer></script>
      {/* 정책/오해 방지: “로그인”이 아니라 “권한/연결”임을 명시 */}
      <div style={{ fontSize: 14, opacity: 0.85, textAlign: "center" }}>
        Google 계정으로 <b>캘린더 읽기 권한</b>을 승인하면 캘린더 목록을 불러옵니다.
      </div>

      <button
        onClick={connect}
        disabled={phase === "requesting"}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "10px 14px",
          borderRadius: 10,
          border: "1px solid #ddd",
          background: "#fff",
          cursor: phase === "requesting" ? "not-allowed" : "pointer",
        }}
        aria-label="Connect Google Calendar"
      >
        {/* Google 로고: “Google 로그인 버튼”처럼 보이지 않게 단순 아이콘 + 연결 문구 */}
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.7 1.22 9.2 3.61l6.87-6.87C35.9 2.4 30.4 0 24 0 14.6 0 6.55 5.38 2.64 13.22l7.98 6.2C12.6 13.5 17.9 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.5 24c0-1.64-.15-3.21-.43-4.73H24v9.03h12.7c-.55 2.97-2.2 5.49-4.67 7.18l7.15 5.55C43.8 36.79 46.5 30.86 46.5 24z"/>
          <path fill="#FBBC05" d="M10.62 28.42A14.5 14.5 0 0 1 9.5 24c0-1.53.26-3.01.72-4.42l-7.98-6.2A23.9 23.9 0 0 0 0 24c0 3.85.92 7.49 2.55 10.78l8.07-6.36z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.77l-7.15-5.55c-2 1.35-4.56 2.15-8.75 2.15-6.06 0-11.37-3.99-13.23-9.5l-8.07 6.36C6.56 42.62 14.58 48 24 48z"/>
        </svg>

        <span>Google 캘린더 연결</span>
      </button>

      <div style={{ fontSize: 13, opacity: 0.85 }}>{status}</div>

      {phase === "requesting" && (
        <>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          <div
            style={{
              width: 18,
              height: 18,
              borderRadius: "50%",
              border: "2px solid #ccc",
              borderTopColor: "#111",
              animation: "spin 0.8s linear infinite",
            }}
          />
        </>
      )}

      {phase === "error" && (
        <div style={{ textAlign: "center" }}>
          <div style={{ marginBottom: 8, color: "#b00020" }}>{error}</div>
          <button onClick={retry}>다시 시도</button>
        </div>
      )}
    </div>
  );
}
