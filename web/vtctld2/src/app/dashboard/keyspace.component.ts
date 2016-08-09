import { ActivatedRoute, Router, ROUTER_DIRECTIVES } from '@angular/router';
import { Component, OnInit, OnDestroy } from '@angular/core';

import { MD_CARD_DIRECTIVES } from '@angular2-material/card';
import { MD_BUTTON_DIRECTIVES } from '@angular2-material/button';

import { Observable } from 'rxjs/Observable';

import { PolymerElement } from '@vaadin/angular2-polymer';

import { AddButtonComponent } from '../shared/add-button.component';
import { DialogComponent } from '../shared/dialog/dialog.component';
import { DialogContent } from '../shared/dialog/dialog-content';
import { DialogSettings } from '../shared/dialog/dialog-settings';
import { NewShardFlags } from '../shared/flags/shard.flags';
import { KeyspaceExtraComponent } from './keyspace-extra.component';
import { KeyspaceService } from '../api/keyspace.service';
import { PrepareResponse } from '../shared/prepare-response';
import { RebuildKeyspaceGraphFlags, RemoveKeyspaceCellFlags, ValidateKeyspaceFlags } from '../shared/flags/keyspace.flags';
import { ShardService } from '../api/shard.service';
import { VtctlService } from '../api/vtctl.service';

@Component({
  moduleId: module.id,
  selector: 'vt-keyspace-view',
  templateUrl: './keyspace.component.html',
  styleUrls: ['../styles/vt.style.css'],
  providers: [
    KeyspaceService,
    ShardService,
    VtctlService
  ],
  directives: [
    ROUTER_DIRECTIVES,
    MD_CARD_DIRECTIVES,
    MD_BUTTON_DIRECTIVES,
    PolymerElement('paper-dialog'),
    DialogComponent,
    AddButtonComponent
  ],
})

export class KeyspaceComponent implements OnInit, OnDestroy {

  private routeSub: any;
  keyspaceName: string;
  shardsReady = false;
  keyspace = {};
  dialogSettings: DialogSettings;
  dialogContent: DialogContent;
  keyspaceExtraComponent = KeyspaceExtraComponent;
  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private keyspaceService: KeyspaceService,
    private vtctlService: VtctlService) {}

  ngOnInit() {
    this.dialogContent = new DialogContent();
    this.dialogSettings = new DialogSettings();
    let paramStream = this.router.routerState.queryParams;
    let routeStream = this.route.url;
    this.routeSub = paramStream.combineLatest(routeStream).subscribe( routeData => {
      let params = routeData[0];
      let path = routeData[1][0].path;
      let keyspaceName = params['keyspace'];
      if (path === 'keyspace' && keyspaceName) {
        this.keyspaceName = keyspaceName;
        this.getKeyspace(this.keyspaceName);
      }
    });
  }

  ngOnDestroy() {
    this.routeSub.unsubscribe();
  }

  getKeyspace(keyspaceName) {
    this.keyspaceService.getKeyspace(keyspaceName).subscribe(keyspaceStream => {
      keyspaceStream.subscribe(keyspace => {
          this.keyspace = keyspace;
      });
    });
  }

  createShard() {
    this.serverCall('CreateShard', 'There was a problem creating {{shard_ref}}:');
  }

  validateKeyspace() {
    this.serverCall('ValidateKeyspace', 'There was a problem validating {{keyspace_name}}:');
  }

  rebuildKeyspace() {
    this.serverCall('RebuildKeyspaceGraph', 'There was a problem rebuilding {{keyspace_name}}:');
  }

  removeKeyspaceCell() {
    this.serverCall('RemoveKeyspaceCell', 'There was a problem removing {{cell_name}}:');
  }

  serverCall(action: string, errorMessage: string) {
    this.vtctlService.serverCall(action, this.dialogContent, this.dialogSettings, errorMessage);
  }

  prepareNewShard() {
    this.dialogSettings = new DialogSettings('Create', this.createShard.bind(this), 'Create a new Shard', '');
    this.dialogSettings.setMessage('Created {{shard_ref}}');
    this.dialogSettings.onCloseFunction = this.refreshKeyspaceView.bind(this);
    let flags = new NewShardFlags(this.keyspaceName).flags;
    this.dialogContent = new DialogContent('shard_ref', flags, {}, this.prepareShard.bind(this));
    this.dialogSettings.toggleModal();
  }

  prepareValidateKeyspace() {
    this.dialogSettings = new DialogSettings('Validate', this.validateKeyspace.bind(this), `Validate ${this.keyspaceName}`, '');
    this.dialogSettings.setMessage('Validated {{keyspace_name}}');
    this.dialogSettings.onCloseFunction = this.refreshKeyspaceView.bind(this);
    let flags = new ValidateKeyspaceFlags(this.keyspaceName).flags;
    this.dialogContent = new DialogContent('keyspace_name', flags, {});
    this.dialogSettings.toggleModal();
  }

  prepareRebuildKeyspaceGraph() {
    this.dialogSettings = new DialogSettings('Rebuild', this.rebuildKeyspace.bind(this), `Rebuild ${this.keyspaceName}`, '');
    this.dialogSettings.setMessage('Rebuilt {{keyspace_name}}');
    this.dialogSettings.onCloseFunction = this.refreshKeyspaceView.bind(this);
    let flags = new RebuildKeyspaceGraphFlags(this.keyspaceName).flags;
    this.dialogContent = new DialogContent('keyspace_name', flags, {});
    this.dialogSettings.toggleModal();
  }

  prepareRemoveKeyspaceCell() {
    this.dialogSettings = new DialogSettings('Remove', this.removeKeyspaceCell.bind(this), `Remove a cell from ${this.keyspaceName}`, '');
    this.dialogSettings.setMessage('Removed {{cell_name}}');
    this.dialogSettings.onCloseFunction = this.refreshKeyspaceView.bind(this);
    let flags = new RemoveKeyspaceCellFlags(this.keyspaceName).flags;
    this.dialogContent = new DialogContent('cell_name', flags, {});
    this.dialogSettings.toggleModal();
  }

  refreshKeyspaceView() {
    this.getKeyspace(this.keyspaceName);
  }

  /*
    Creates a shard reference from the keyspacename paired with the lower and
    upper bounds. Sets all other flag values to the empty string so they don't
    end up in the request.
  */
  prepareShard(flags) {
    let shardName = this.getName(flags['lower_bound'].getStrValue(), flags['upper_bound'].getStrValue());
    flags['shard_ref'].setValue(flags['keyspace_name'].getStrValue() + '/' + shardName);
    flags['keyspace_name'].setValue('');
    flags['lower_bound'].setValue('');
    flags['upper_bound'].setValue('');
    return new PrepareResponse(true, flags);
  }

  // Functions for parsing shardName
  getName(lowerBound, upperBound) {
    this.dialogContent.setName(lowerBound + '-' + upperBound);
    return this.dialogContent.getName();
  }

  canDeactivate(): Observable<boolean> | boolean {
    return !this.dialogSettings.pending;
  }

  noShards() {
    if (this.keyspace === undefined) {
      return false;
    }
    if (this.keyspace['servingShards'] === undefined || this.keyspace['nonservingShards'] === undefined) {
      return false;
    }
    if (this.keyspace['servingShards'].length === 0 && this.keyspace['nonservingShards'].length === 0) {
      return true;
    }
    return false;
  }
}