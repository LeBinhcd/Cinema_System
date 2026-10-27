import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';

const STREAM = 'https://stream.mux.com/kimF2ha9zLrX64H00UgLGPflCzNtl1T0215MlAmeOztv8.m3u8';

export function BackgroundVideo() {
  const videoRef = useRef(null);
  const [videoReady, setVideoReady] = useState(false);
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    let hls;
    const ready = () => { setVideoReady(true); video.play().catch(() => {}); };
    video.addEventListener('canplay', ready);
    if (video.canPlayType('application/vnd.apple.mpegurl')) video.src = STREAM;
    else if (Hls.isSupported()) {
      hls = new Hls({ enableWorker: true, lowLatencyMode: true });
      hls.on(Hls.Events.MEDIA_ATTACHED, () => hls.loadSource(STREAM));
      hls.on(Hls.Events.MANIFEST_PARSED, ready);
      hls.attachMedia(video);
    }
    return () => { video.removeEventListener('canplay', ready); hls?.destroy(); };
  }, []);
  return <div className="absolute inset-0 overflow-hidden pointer-events-none">
    <div className="hero-fallback" aria-hidden="true" />
    <video ref={videoRef} autoPlay muted loop playsInline className={`hero-video w-full h-full object-cover ${videoReady ? 'is-ready' : ''}`} />
    <div className="hero-vignette" aria-hidden="true" />
  </div>;
}
