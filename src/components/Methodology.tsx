import { ArrowSquareOut } from "@phosphor-icons/react/dist/ssr";
import type { Stats, Overlay } from "@/lib/types";
import { peso, num } from "@/lib/format";

export default function Methodology({ stats, overlay }: { stats: Stats; overlay: Overlay }) {
  return (
    <section id="methodology" className="scroll-mt-20">
      <div className="mb-6">
        <p className="eyebrow">How this was built, and its limits</p>
        <h2 className="mt-1 font-display text-2xl font-bold text-text-primary md:text-3xl">Methodology</h2>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <Card title="What this is, and is not">
          <p>
            A map of public records. Every node and edge is either a recorded fact from the DPWH transparency dataset
            or a curated, source-linked action (a license revocation, a blacklist, a court filing, an audit flag). The
            graph computes descriptive statistics, concentration, co-award structure, who won the most. It does not
            establish guilt, and it is not a list of wrongdoers. Charges are allegations under the presumption of
            innocence.
          </p>
        </Card>

        <Card title="Data sources">
          <ul>
            <li>
              <strong>DPWH contracts.</strong> {num(stats.totals.contracts)} contracts worth {peso(stats.totals.total_value)},
              from the DPWH Transparency Portal via BetterGov.PH{" "}
              <Src url={stats.source.url} label="HuggingFace dataset, CC0" />. License: {stats.source.license}.
            </li>
            <li>
              <strong>Official actions.</strong> Curated and source-linked: PCAB Board Resolution 075, Ombudsman and
              Sandiganbayan filings, DPWH Secretary orders, COA fraud audit reports, SEC resolutions.
            </li>
            <li>
              <strong>News tagging.</strong> Recent coverage matched by exact firm name to the firms named in the flood-control reporting, each
              linking its source article.
            </li>
          </ul>
        </Card>

        <Card title="Entity resolution">
          <p>
            The DPWH contractor field is messy: the same firm appears with and without its numeric id, inside joint
            ventures (split on &quot;/&quot;), and with &quot;formerly&quot; and &quot;[REVOKED]&quot; notes. We resolve
            each firm to its DPWH id (or a normalized name when no id is present), collapsing {num(stats.totals.contracts)} contract
            rows to <strong>{num(stats.totals.contractors)} distinct firms</strong>. Joint ventures become recorded co-award
            edges. For example, the {stats.revoked.contracts.toLocaleString()} contracts tagged &quot;[REVOKED]&quot; resolve
            to just <strong>{stats.revoked.firms} firms</strong> ({peso(stats.revoked.value)}). A naive count of the raw
            strings would report 256.
          </p>
        </Card>

        <Card title="Confidence tiers">
          <p>An inferred link never looks like a recorded one.</p>
          <ul>
            <li><strong>Recorded</strong> (solid line): a contract award, joint venture, revoked license, blacklist, court filing, or a source-linked person, with a source.</li>
            <li><strong>Inferred from records</strong> (curved, lighter): not stated but computed, such as two firms that are both top awardees in the same district offices.</li>
            <li><strong>Predicted</strong> (faintest, off by default): a Node2Vec statistical similarity in bidding footprint between firms with no recorded joint venture. Not evidence of a relationship, and unverified against any registry.</li>
            <li><strong>Possible namesake</strong>: a shared surname is not a relationship. Not shown in this release; reserved for a future human-verified layer.</li>
          </ul>
        </Card>

        <Card title="The numbers">
          <p>
            Node size is not an importance score, but the recorded flood-control contract value. Concentration uses the
            Herfindahl-Hirschman Index per district office; {stats.concentration.concentrated_fc_deos} flood-control offices exceed
            2,500 (the US DOJ &quot;highly concentrated&quot; threshold). Brokerage (betweenness), influence (PageRank), and
            co-award communities (Louvain, {stats.communities} groups) are computed offline with networkx and baked into the graph.
            Flood control is pinned to the exact DPWH category, {num(stats.flood_control.contracts)} contracts worth {peso(stats.flood_control.value)}.
          </p>
        </Card>

        <Card title="Network analysis methods">
          <p>
            Computed offline with networkx and gensim, seeded for reproducibility, and baked as JSON.
            <strong> Temporal:</strong> per-year value, the named firms&apos; share (contract value split equally among
            joint awardees so shares sum to 100%), newcomer share, and the cumulative joint-venture network.
            <strong> Patterns:</strong> descriptive indicators with stated thresholds, in the spirit of the OECD
            guidelines for fighting bid rigging in public procurement; a zero result is reported as tested.
            <strong> Predicted ties:</strong> Node2Vec embeddings (64 dims, seed 42) over the firm-office graph;
            cosine similarity between firms with no recorded joint venture, corroborated by Adamic-Adar. Statistical
            similarity only, never presented as a relationship.
          </p>
        </Card>

        <Card title="Verification and limits">
          <p>
            Primary-source-or-omit: an official action or person enters the graph only if it traces to a primary or
            primary-citing source. Firms without a confirmed action carry recorded facts only. The person layer is
            curated and source-linked, not scraped. Not yet joined, stated plainly: bulk SALN wealth and SOCE
            campaign-finance records (neither is available as machine-readable public data today; the one
            campaign-finance link shown is individually sourced), and the PhilGEPS cross-check. Oversight bodies:{" "}
            {overlay.investigation.map((b, i) => (
              <span key={b.body}>{i > 0 ? ", " : ""}{b.body}</span>
            ))}.
          </p>
        </Card>
      </div>

      <div className="mt-6 rounded-xl border border-hairline bg-surface-2 p-5">
        <p className="text-sm leading-relaxed text-text-secondary">
          All data sourced from public records (COA, SEC, DBM, PSA, BSP, SALN disclosures). This tool computes statistical
          indicators only. Specific allegations, if any, require independent investigation and corroboration.
        </p>
      </div>

      <div className="mt-5">
        <p className="eyebrow mb-2">Related projects</p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <Src url="https://visualizations.bettergov.ph/flood" label="BetterGov.PH flood visualizations" />
          <Src url="https://www.rappler.com/newsbreak/investigative/politicians-government-contractors-connections-map/" label="Rappler Politicontractors" />
          <Src url="https://infrawatchph.org/home/contractors" label="InfraWatch PH" />
          <Src url="https://moneypolitics.pcij.org/" label="PCIJ MoneyPolitics" />
          <Src url="https://aleph.occrp.org/" label="OCCRP Aleph" />
          <Src url="https://littlesis.org/" label="LittleSis" />
        </div>
      </div>
    </section>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="prose-ledger rounded-xl border border-hairline bg-surface p-5">
      <h3 className="mb-2 font-display text-base font-semibold text-text-primary">{title}</h3>
      {children}
    </div>
  );
}

function Src({ url, label }: { url: string; label: string }) {
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1">
      {label} <ArrowSquareOut size={12} />
    </a>
  );
}
