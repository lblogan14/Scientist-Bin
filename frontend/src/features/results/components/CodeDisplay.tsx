import { Highlight, themes } from "prism-react-renderer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface CodeDisplayProps {
  code: string | null;
}

export function CodeDisplay({ code }: CodeDisplayProps) {
  if (!code) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground text-sm">
            No code generated yet.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Generated Code</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          <Highlight theme={themes.nightOwl} code={code} language="python">
            {({ style, tokens, getLineProps, getTokenProps }) => (
              <pre
                className="overflow-x-auto rounded-md p-4 font-mono text-xs"
                style={style}
              >
                {tokens.map((line, i) => (
                  <div key={i} {...getLineProps({ line })}>
                    <span className="mr-4 inline-block w-8 text-right opacity-40 select-none">
                      {i + 1}
                    </span>
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                  </div>
                ))}
              </pre>
            )}
          </Highlight>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
