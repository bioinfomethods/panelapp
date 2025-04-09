export interface DeleteComment {
  comment: string;
}

export interface UpdateRating {
  rating: string;
  comment?: string;
}

export interface UpdateModeOfInheritance {
  moi: string;
  comment?: string;
}

export interface UpdateModeOfPathogenicity {
  mop: string;
  comment?: string;
}

export interface UpdatePublications {
  publications: string[];
  comment?: string;
}

export interface UpdatePhenotypes {
  phenotypes: string[];
  comment?: string;
}

export interface UpdateReady {
  ready: boolean;
  comment?: string;
}

export interface GeneFeedback {
  panelGeneTestId: string;
  by: string;
  deleteComments?: DeleteComment[];
  tags?: string[];
  rating?: UpdateRating;
  moi?: UpdateModeOfInheritance;
  mop?: UpdateModeOfPathogenicity;
  publications?: UpdatePublications;
  phenotypes?: UpdatePhenotypes;
  ready?: UpdateReady;
}
