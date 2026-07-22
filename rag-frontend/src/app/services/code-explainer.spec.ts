import { TestBed } from '@angular/core/testing';

import { CodeExplainer } from './code-explainer';

describe('CodeExplainer', () => {
  let service: CodeExplainer;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(CodeExplainer);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
