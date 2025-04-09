export interface Provenance {
  createdBy: string;
}

export type Id = string;
export type TestId = string;

// Entity is uniquely identified within PanelApp
export interface Identifiable {
  id: Id;
}

// Entity is uniquely identified within a single test
export interface TestIdentifiable {
  testId: TestId;
}
