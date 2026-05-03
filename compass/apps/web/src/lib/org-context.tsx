"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface OrgContextValue {
  orgId: string | null;
  orgName: string | null;
  orgRole: string | null;
  setOrg: (id: string, name: string, role: string) => void;
  clearOrg: () => void;
}

const OrgContext = createContext<OrgContextValue>({
  orgId: null,
  orgName: null,
  orgRole: null,
  setOrg: () => {},
  clearOrg: () => {},
});

const STORAGE_KEY = "compass_org_id";
const STORAGE_NAME = "compass_org_name";
const STORAGE_ROLE = "compass_org_role";

export function OrgProvider({ children }: { children: ReactNode }) {
  const [orgId,   setOrgId]   = useState<string | null>(null);
  const [orgName, setOrgName] = useState<string | null>(null);
  const [orgRole, setOrgRole] = useState<string | null>(null);

  useEffect(() => {
    setOrgId(localStorage.getItem(STORAGE_KEY));
    setOrgName(localStorage.getItem(STORAGE_NAME));
    setOrgRole(localStorage.getItem(STORAGE_ROLE));
  }, []);

  const setOrg = (id: string, name: string, role: string) => {
    localStorage.setItem(STORAGE_KEY, id);
    localStorage.setItem(STORAGE_NAME, name);
    localStorage.setItem(STORAGE_ROLE, role);
    setOrgId(id);
    setOrgName(name);
    setOrgRole(role);
  };

  const clearOrg = () => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_NAME);
    localStorage.removeItem(STORAGE_ROLE);
    setOrgId(null);
    setOrgName(null);
    setOrgRole(null);
  };

  return (
    <OrgContext.Provider value={{ orgId, orgName, orgRole, setOrg, clearOrg }}>
      {children}
    </OrgContext.Provider>
  );
}

export function useOrg() {
  return useContext(OrgContext);
}

export function getOrgId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(STORAGE_KEY);
}
