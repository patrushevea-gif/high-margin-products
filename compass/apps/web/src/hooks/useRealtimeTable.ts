import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { supabase } from "@/lib/supabase";

type RealtimeEvent = "INSERT" | "UPDATE" | "DELETE" | "*";

interface Options {
  /** TanStack Query keys to invalidate on any change */
  invalidateKeys: string[][];
  event?: RealtimeEvent;
}

/**
 * Subscribe to a Supabase Realtime channel for a given table.
 * Invalidates TanStack Query caches on every matching event.
 * No-ops gracefully when Supabase client is not configured.
 */
export function useRealtimeTable(table: string, opts: Options) {
  const qc = useQueryClient();
  const channelRef = useRef<ReturnType<NonNullable<typeof supabase>["channel"]> | null>(null);

  useEffect(() => {
    if (!supabase) return; // fallback: polling handles updates

    const channel = supabase
      .channel(`realtime:${table}`)
      .on(
        // @ts-expect-error — supabase types require literal "postgres_changes"
        "postgres_changes",
        { event: opts.event ?? "*", schema: "public", table },
        () => {
          opts.invalidateKeys.forEach((key) => {
            qc.invalidateQueries({ queryKey: key });
          });
        }
      )
      .subscribe();

    channelRef.current = channel;

    return () => {
      channel.unsubscribe();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [table]);
}
