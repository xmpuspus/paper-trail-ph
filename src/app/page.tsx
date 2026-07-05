import Header from "@/components/common/Header";
import Footer from "@/components/common/Footer";
import Hero from "@/components/Hero";
import StoryRail from "@/components/StoryRail";
import Explorer from "@/components/Explorer";
import Methodology from "@/components/Methodology";
import { getStats, getScandalGraph, getOverlay, getInNews } from "@/lib/data";

export default function Home() {
  const stats = getStats();
  const scandalGraph = getScandalGraph();
  const overlay = getOverlay();
  const inNews = getInNews();

  return (
    <>
      <Header />
      <main id="main">
        <div className="mx-auto max-w-content px-4 md:px-6">
          <Hero stats={stats} />

          <div className="mt-16 md:mt-24">
            <StoryRail scandalGraph={scandalGraph} overlay={overlay} inNews={inNews} stats={stats} />
          </div>

          <div className="mt-16 md:mt-24">
            <div className="mb-6">
              <p className="eyebrow">Search-first</p>
              <h2 className="mt-1 font-display text-2xl font-bold text-text-primary md:text-3xl">Explore the graph</h2>
              <p className="mt-2 max-w-2xl text-sm text-text-secondary">
                Search {stats.totals.contractors.toLocaleString()} firms and {stats.totals.district_offices} district offices by name,
                by an owner or officer named in the records, or by a former company name. Select a node to see its record, its
                recorded joint ventures, the official actions on file, and the sources.
              </p>
            </div>
            <Explorer scandalGraph={scandalGraph} overlay={overlay} inNews={inNews} stats={stats} />
          </div>

          <div className="mt-16 md:mt-24">
            <Methodology stats={stats} overlay={overlay} />
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
