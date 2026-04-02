import { Suspense } from "react";
import { Outlet } from "react-router";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Header } from "@/components/layout/Header";
import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";
import { LoadingSpinner } from "@/components/feedback/LoadingSpinner";

export function Layout() {
  return (
    <SidebarProvider>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-background focus:p-2 focus:text-sm focus:shadow"
      >
        Skip to content
      </a>
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-1 flex-col">
          <Header />
          <main id="main-content" className="flex-1 p-6">
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner />}>
                <Outlet />
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
