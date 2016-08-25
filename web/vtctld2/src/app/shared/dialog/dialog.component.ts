import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ROUTER_DIRECTIVES } from '@angular/router';

import { DialogContent } from './dialog-content';
import { DialogSettings } from './dialog-settings';
import { KeyspaceService } from '../../api/keyspace.service';
import { TabletService } from '../../api/tablet.service';

@Component({
  selector: 'vt-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.css', '../../styles/vt.style.css'],
  providers: [
    KeyspaceService,
    TabletService
  ],
  directives: [
    ROUTER_DIRECTIVES,
  ],
})
export class DialogComponent {
  keyspaces = [];
  extraContentReference: any;
  @Input() dialogContent: DialogContent;
  @Input() dialogSettings: DialogSettings;
  @Output() close = new EventEmitter();


  typeSelected(paramName, e) {
    // Polymer event syntax, waiting on Material2 implementation of dropdown.
    this.dialogContent.setParam(paramName, e.detail.item.__dom.firstChild.data);
  }

  cancelDialog() {
    this.dialogSettings.toggleModal();
    this.close.emit({});
  }

  closeDialog() {
    if (this.dialogSettings.onCloseFunction) {
      this.dialogSettings.onCloseFunction(this.dialogContent);
    }
    this.dialogSettings.toggleModal();
    this.close.emit({});
  }

  sendAction() {
    let resp = this.dialogContent.prepare();
    if (resp.success) {
      this.dialogSettings.actionFunction();
    } else {
      this.dialogSettings.setMessage(`There was a problem preparing ${this.dialogContent.getName()}: ${resp.message}`);
    }
    this.dialogSettings.dialogForm = false;
    this.dialogSettings.dialogLog = true;
  }

  getCmd() {
    let preppedFlags = this.dialogContent.prepare(false).flags;
    let sortedFlags = this.dialogContent.getFlags(preppedFlags);
    return this.dialogContent.getPostBody(sortedFlags);
  }
  logToArray(logText) {
    return logText.split('\n');
  }
}
