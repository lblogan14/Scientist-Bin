import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { MarkdownRenderer } from "@/components/shared/MarkdownRenderer";
import { getArtifactDownloadUrl } from "@/lib/api-client";
import type { SummaryReportSections } from "@/types/api";

interface SummaryTabProps {
  /** Full markdown summary report */
  summaryReport?: string | null;
  /** Structured report sections for accordion view */
  sections?: SummaryReportSections | null;
  experimentId: string;
}

const SECTION_ORDER: { key: keyof SummaryReportSections; label: string }[] = [
  { key: "executive_summary", label: "Executive Summary" },
  { key: "dataset_overview", label: "Dataset Overview" },
  { key: "methodology", label: "Methodology" },
  { key: "model_comparison_table", label: "Model Comparison" },
  { key: "cv_stability_analysis", label: "CV Stability Analysis" },
  { key: "best_model_analysis", label: "Best Model Analysis" },
  { key: "feature_importance_analysis", label: "Feature Importance" },
  { key: "hyperparameter_analysis", label: "Hyperparameter Analysis" },
  { key: "error_analysis", label: "Error Analysis" },
  { key: "conclusions", label: "Conclusions" },
  { key: "reproducibility_notes", label: "Reproducibility Notes" },
];

export function SummaryTab({
  summaryReport,
  sections,
  experimentId,
}: SummaryTabProps) {
  if (!summaryReport && !sections) {
    return (
      <p className="text-muted-foreground text-sm">
        No summary report available for this experiment.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" asChild>
          <a href={getArtifactDownloadUrl(experimentId, "summary")} download>
            <Download className="mr-1.5 size-3.5" />
            Download Report
          </a>
        </Button>
      </div>

      {/* Structured accordion view if sections available */}
      {sections ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">
              {sections.title || "Summary Report"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="multiple" defaultValue={["executive_summary"]}>
              {SECTION_ORDER.map(({ key, label }) => {
                const content = sections[key];
                if (
                  !content ||
                  (typeof content === "string" && !content.trim())
                )
                  return null;
                return (
                  <AccordionItem key={key} value={key}>
                    <AccordionTrigger>{label}</AccordionTrigger>
                    <AccordionContent>
                      <MarkdownRenderer
                        content={
                          typeof content === "string"
                            ? content
                            : JSON.stringify(content)
                        }
                      />
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
              {sections.recommendations?.length > 0 && (
                <AccordionItem value="recommendations">
                  <AccordionTrigger>Recommendations</AccordionTrigger>
                  <AccordionContent>
                    <ul className="list-disc space-y-1 pl-4 text-sm">
                      {sections.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </AccordionContent>
                </AccordionItem>
              )}
            </Accordion>
          </CardContent>
        </Card>
      ) : (
        /* Full markdown fallback */
        summaryReport && (
          <Card>
            <CardContent className="pt-6">
              <MarkdownRenderer content={summaryReport} />
            </CardContent>
          </Card>
        )
      )}
    </div>
  );
}
