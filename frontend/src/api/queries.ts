import { queryOptions, useQuery } from "@tanstack/react-query";
import { getJson } from "./client";
import type { Accuracy, Decision, Horizon, Meta, Vintages } from "./types";

const STATIC_DATA = { staleTime: Infinity, gcTime: 30 * 60 * 1000 } as const;

export const metaQuery = () =>
  queryOptions({ queryKey: ["meta"], queryFn: ({ signal }) => getJson<Meta>("/meta", {}, signal), ...STATIC_DATA });

export const decisionQuery = (day: string, cutoff: string) =>
  queryOptions({
    queryKey: ["decision", day, cutoff],
    queryFn: ({ signal }) => getJson<Decision>("/decision", { day, cutoff }, signal),
    ...STATIC_DATA,
  });

export const vintagesQuery = (day: string, cutoff: string) =>
  queryOptions({
    queryKey: ["vintages", day, cutoff],
    queryFn: ({ signal }) => getJson<Vintages>("/vintages", { day, cutoff }, signal),
    ...STATIC_DATA,
  });

export const accuracyQuery = (cutoff: string) =>
  queryOptions({
    queryKey: ["accuracy", cutoff],
    queryFn: ({ signal }) => getJson<Accuracy>("/accuracy", { cutoff }, signal),
    ...STATIC_DATA,
  });

export const horizonQuery = (cutoff: string) =>
  queryOptions({
    queryKey: ["horizon", cutoff],
    queryFn: ({ signal }) => getJson<Horizon>("/horizon", { cutoff }, signal),
    ...STATIC_DATA,
  });

export const useMeta = () => useQuery(metaQuery());
