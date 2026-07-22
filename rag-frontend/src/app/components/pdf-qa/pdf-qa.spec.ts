import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PdfQa } from './pdf-qa';

describe('PdfQa', () => {
  let component: PdfQa;
  let fixture: ComponentFixture<PdfQa>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PdfQa],
    }).compileComponents();

    fixture = TestBed.createComponent(PdfQa);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
