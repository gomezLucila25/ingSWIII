import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ActivatedRoute } from '@angular/router';

import { MyUserComponent } from './my-user.component';

describe('MyUserComponent', () => {
  let component: MyUserComponent;
  let fixture: ComponentFixture<MyUserComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MyUserComponent, HttpClientTestingModule],
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => null } } } }
      ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MyUserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
