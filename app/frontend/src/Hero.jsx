import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { ArrowRight, Check } from 'lucide-react';

const BUTTON_TEXT = 'Get early access';
const DEFAULT_PLACEHOLDER = 'Enter Your Email Here For Early Access';
const SUCCESS_PLACEHOLDER = 'You Will Receive Notifications By Email';

function useTypewriter(active, text) {
  const [value, setValue] = useState('');
  useEffect(() => { if (!active) return undefined; setValue(''); let i = 0; const timer = setInterval(() => { i += 1; setValue(text.slice(0, i)); if (i >= text.length) clearInterval(timer); }, 60); return () => clearInterval(timer); }, [active, text]);
  return value;
}

export function Hero() {
  const [open, setOpen] = useState(false); const [submitted, setSubmitted] = useState(false); const [email, setEmail] = useState('');
  const placeholder = useTypewriter(open, submitted ? SUCCESS_PLACEHOLDER : DEFAULT_PLACEHOLDER);
  useEffect(() => { if (!submitted) return undefined; const timer = setTimeout(() => { setSubmitted(false); setOpen(false); setEmail(''); }, 4000); return () => clearTimeout(timer); }, [submitted]);
  const submit = (event) => { event.preventDefault(); if (email.trim()) setSubmitted(true); };
  return <section className="relative flex-1 flex flex-col items-center justify-center px-6"><div className="relative z-10 text-center max-w-5xl mx-auto flex flex-col items-center justify-center w-full gap-12">
    <div><motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .1 }} className="text-white/80 text-[10px] md:text-[11px] font-medium tracking-[0.2em] uppercase mb-4">BUILD A NO-CODE AI APP IN MINUTES</motion.p><motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }} style={{ fontFamily: "'Instrument Serif', serif" }} className="text-4xl md:text-[64px] font-medium tracking-[-0.01em] leading-[1.1] mb-6 bg-gradient-to-b from-white via-white/95 to-white/70 bg-clip-text text-transparent max-w-4xl">A new way to think and create <br className="hidden md:block"/>with computers</motion.h1></div>
    <motion.div initial={{ opacity: 0, scale: .95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: .4 }} className="min-h-[50px] mt-2"><AnimatePresence mode="wait">{!open ? <motion.button key="button" initial={{ opacity: 0, scale: .95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: .95 }} onClick={() => setOpen(true)} className="px-10 py-3 text-[14px] font-medium border border-white/10 rounded-full hover:border-white/30 hover:bg-white/[0.02] transition-all duration-300 text-white/90 backdrop-blur-sm cursor-pointer">{BUTTON_TEXT}</motion.button> : <motion.form key="form" onSubmit={submit} initial={{ opacity: 0, scale: .95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: .95 }} className="flex items-center gap-2 pl-5 pr-1.5 py-1.5 text-[14px] font-medium border border-white/20 rounded-full bg-white/[0.02] backdrop-blur-sm w-full max-w-[320px] focus-within:border-white/40 transition-colors duration-300"><input autoFocus type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder={placeholder} className="min-w-0 flex-1 bg-transparent outline-none text-white placeholder:text-white/45"/><button aria-label="Submit email" className="shrink-0 rounded-full p-2 text-white hover:bg-white/10 cursor-pointer">{submitted ? <Check size={17}/> : <ArrowRight size={17}/>}</button></motion.form>}</AnimatePresence></motion.div>
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: .8 }}><a href="#demo" className="text-white/80 hover:text-white/40 transition-colors duration-300 text-[13px] font-medium tracking-wide">Play Video Demo</a></motion.div>
  </div></section>;
}
