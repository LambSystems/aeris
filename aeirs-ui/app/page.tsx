"use client"

import Link from "next/link"
import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"

export default function Page() {
  const [activeTab, setActiveTab] = useState("home")

  const homeRef = useRef<HTMLDivElement>(null)
  const featuresRef = useRef<HTMLDivElement>(null)
  const impactRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const sections = [
      { id: "home", ref: homeRef },
      { id: "features", ref: featuresRef },
      { id: "impact", ref: impactRef },
    ]

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const id = entry.target.getAttribute("data-section")
            if (id) setActiveTab(id)
          }
        })
      },
      {
        threshold: 0.3,
        rootMargin: "-20% 0px -40% 0px",
      },
    )

    sections.forEach((sec) => sec.ref.current && observer.observe(sec.ref.current))
    return () => observer.disconnect()
  }, [])

  return (
    <div className="h-screen w-screen relative overflow-hidden text-white">
      <video autoPlay loop muted playsInline className="absolute inset-0 w-full h-full object-cover">
        <source src="/earth.mp4" type="video/mp4" />
      </video>

      <div className="absolute inset-0 bg-black/50" />

      <div className="absolute top-0 left-0 right-0 z-20 flex justify-between items-center px-10 py-6">
        <h1 className="text-2xl font-semibold">AEIRS</h1>

        <div className="hidden md:flex gap-10 text-sm relative">
          {["home", "features", "impact"].map((tab) => (
            <div key={tab} className="relative">
              <button
                type="button"
                onClick={() => {
                  const map = { home: homeRef, features: featuresRef, impact: impactRef }
                  map[tab as keyof typeof map]?.current?.scrollIntoView({ behavior: "smooth" })
                }}
                className={`pb-2 capitalize transition ${
                  activeTab === tab ? "text-blue-300" : "text-white/70"
                }`}
              >
                {tab}
              </button>

              {activeTab === tab && (
                <motion.div
                  layoutId="underline"
                  className="absolute bottom-0 left-0 right-0 h-[2px] bg-blue-400"
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="relative z-10 h-full overflow-y-scroll snap-y snap-mandatory">
        <div ref={homeRef} data-section="home" className="h-screen flex items-center px-16 snap-start">
          <div>
            <h1 className="text-5xl font-bold mb-6">
              Save Your Environment.
            </h1>
            <Link
              href="/live"
              prefetch={false}
              className="inline-block bg-white/10 hover:bg-white/20 px-6 py-3 rounded-full transition-colors"
            >
              Step into AEIRS
            </Link>
          </div>
        </div>

        <div
          ref={featuresRef}
          data-section="features"
          className="min-h-screen flex items-center px-16 snap-start"
        >
          <div className="w-full max-w-6xl">
            <h1 className="text-6xl font-bold mb-6">How AEIRS Thinks</h1>
            <p className="text-white/70 mb-16 max-w-2xl">
              A continuous intelligence loop: sensing the environment, interpreting context, and delivering
              real-time guidance in milliseconds.
            </p>

            <div className="relative">
              <div className="absolute left-1/2 top-0 h-full w-[2px] bg-gradient-to-b from-transparent via-blue-400 to-transparent opacity-70" />

              <div className="space-y-20">
                {[
                  ["Capture", "Live camera streams environmental data continuously."],
                  ["Detect", "Objects are identified and tracked in real time."],
                  ["Analyze", "Air quality and location combine into contextual signals."],
                  ["Reason", "AI evaluates risk and situational meaning."],
                  ["Respond", "Clear, actionable recommendations appear instantly."],
                ].map(([title, desc], i) => {
                  const left = i % 2 === 0

                  return (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 60 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="relative flex items-center"
                    >
                      <div className="absolute left-1/2 -translate-x-1/2 w-4 h-4 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50" />

                      <div
                        className={`
                            w-1/2 p-6 rounded-2xl backdrop-blur-xl border border-white/10
                            bg-gradient-to-br from-blue-500/20 to-cyan-400/10
                            shadow-lg shadow-blue-400/20
                            hover:shadow-blue-400/40 hover:scale-[1.03]
                            transition duration-300
                            ${left ? "mr-auto pr-10 text-right" : "ml-auto pl-10"}
                          `}
                      >
                        <h2 className="text-lg font-semibold mb-2 text-blue-300">{title}</h2>
                        <p className="text-sm text-white/70">{desc}</p>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            </div>

            <div className="mt-16 text-center text-white/40 text-sm">
              A loop that never stops learning — adapting to every moment.
            </div>
          </div>
        </div>

        <div ref={impactRef} data-section="impact" className="min-h-screen flex items-center px-16 snap-start">
          <div className="w-full max-w-6xl">
            <h1 className="text-6xl font-bold mb-6">From Awareness → Action</h1>

            <p className="text-white/70 mb-16 max-w-2xl">
              AEIRS turns invisible environmental signals into real-time action, empowering people to stay safe,
              make smarter decisions, and build lasting environmental awareness.
            </p>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                ["Real-Time Safety", "Get immediate alerts so you can stay safe when conditions change."],
                ["Risk Prevention", "Avoid danger before it becomes a problem."],
                ["Prepared Living", "Simple guidance to help you set up a safer home environment."],
                ["Environmental Visibility", "Make invisible risks visible and actionable."],
                ["Smart Mobility", "Encourage sustainable movement decisions."],
                ["Continuous Intelligence", "Build long-term environmental insights."],
              ].map(([title, desc], i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.9 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1 }}
                  className="
                      p-6 rounded-2xl
                      bg-gradient-to-br from-purple-500/20 via-blue-500/10 to-cyan-400/10
                      border border-white/10
                      backdrop-blur-xl
                      shadow-lg shadow-blue-400/10
                      hover:-translate-y-3 hover:shadow-blue-400/40
                      transition duration-300
                    "
                >
                  <h2 className="text-lg font-semibold mb-3 text-white">{title}</h2>
                  <p className="text-sm text-white/70">{desc}</p>
                </motion.div>
              ))}
            </div>

            <div className="mt-20 flex flex-wrap gap-4">
              <Link
                href="/live"
                prefetch={false}
                className="inline-block bg-white text-neutral-900 hover:bg-white/90 px-8 py-3 rounded-full font-medium transition-colors"
              >
                Open live vision
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
