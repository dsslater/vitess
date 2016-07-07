import { Component, OnInit} from '@angular/core';
import { ROUTER_DIRECTIVES } from '@angular/router';
import { KeyspaceService } from '../shared/keyspaceService/keyspace.service';
import { Keyspace } from '../shared/keyspaceObject/keyspace'
import { MD_CARD_DIRECTIVES } from '@angular2-material/card';
import { MD_BUTTON_DIRECTIVES } from '@angular2-material/button';
import { MdIcon, MdIconRegistry } from '@angular2-material/icon';
import { NewKeyspaceComponent } from './NewKeyspace/newkeyspace.component'
import { Dialog } from 'primeng/primeng';
import {Button} from 'primeng/primeng';


@Component({
  moduleId: module.id,
  selector: 'vt-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
  providers: [
              KeyspaceService,
              MdIconRegistry],
  directives: [
              NewKeyspaceComponent,
              ROUTER_DIRECTIVES,
              MD_CARD_DIRECTIVES,
              MD_BUTTON_DIRECTIVES,
              MdIcon,
              Dialog,
              Button],
  
})
export class DashboardComponent implements OnInit{
  title = 'Vitess Control Panel';
  keyspaces = [];
  openForm = false;
  keyspacesReady=false;

  toggleForm() {
    console.log("Was:", this.openForm, "   Now this: ", !this.openForm);
    this.openForm = !this.openForm;
  }
  updateOpen(event) {
    this.toggleForm();
  }
  constructor(private keyspaceService: KeyspaceService) { 
    
  }

  ngOnInit() {
    this.getKeyspaces();
  }

  getKeyspaces() {
    this.keyspaceService.getKeyspaces().subscribe(keyspaces => {
      this.keyspaces = keyspaces;
      this.keyspacesReady = true;
    });
  }

   display: boolean = false;

    showDialog() {
        this.display = true;
    }
}
