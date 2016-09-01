#!/usr/bin/env python
"""A vtctld2 webdriver test."""

import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
import unittest

from vtproto import vttest_pb2
from vttest import environment as vttest_environment
from vttest import local_database
from vttest import mysql_flavor

import environment
import utils


def setUpModule():
  try:
    if utils.options.xvfb:
      try:
        # This will be killed automatically by utils.kill_sub_processes()
        utils.run_bg(['Xvfb', ':15', '-ac'])
        os.environ['DISPLAY'] = ':15'
      except OSError as err:
        # Despite running in background, utils.run_bg() will throw immediately
        # if the Xvfb binary is not found.
        logging.error(
            "Can't start Xvfb (will try local DISPLAY instead): %s", err)
  except:
    tearDownModule()
    raise


def tearDownModule():
  utils.required_teardown()
  if utils.options.skip_teardown:
    return
  utils.remove_tmp_files()


class TestVtctldWeb(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    """Set up two keyspaces: one unsharded, one with two shards."""
    if os.environ.get('CI') == 'true' and os.environ.get('TRAVIS') == 'true':
      username = os.environ['SAUCE_USERNAME']
      access_key = os.environ['SAUCE_ACCESS_KEY']
      capabilities = {}
      capabilities['tunnel-identifier'] = os.environ['TRAVIS_JOB_NUMBER']
      capabilities['build'] = os.environ['TRAVIS_BUILD_NUMBER']
      capabilities['platform'] = 'Linux'
      capabilities['browserName'] = 'chrome'
      hub_url = '%s:%s@localhost:4445' % (username, access_key)
      cls.driver = webdriver.Remote(
          desired_capabilities=capabilities,
          command_executor='http://%s/wd/hub' % hub_url)
    else:
      os.environ['webdriver.chrome.driver'] = os.path.join(
          os.environ['VTROOT'], 'dist')
      # Only testing against Chrome for now
      cls.driver = webdriver.Chrome()

    topology = vttest_pb2.VTTestTopology()
    topology.cells.append('test')
    keyspace = topology.keyspaces.add(name='test_keyspace')
    keyspace.replica_count = 2
    keyspace.rdonly_count = 2
    keyspace.shards.add(name='-80')
    keyspace.shards.add(name='80-')
    keyspace2 = topology.keyspaces.add(name='test_keyspace2')
    keyspace2.shards.add(name='0')
    keyspace2.replica_count = 2
    keyspace2.rdonly_count = 1

    port = environment.reserve_ports(1)
    vttest_environment.base_port = port
    mysql_flavor.set_mysql_flavor(None)

    cls.db = local_database.LocalDatabase(
        topology, '', False, None,
        os.path.join(os.environ['VTTOP'], 'web/vtctld2/dist'),
        os.path.join(os.environ['VTTOP'], 'test/vttest_schema/default'))
    cls.db.setup()
    cls.vtctld_addr = 'http://localhost:%d' % cls.db.config()['port']
    utils.pause('Paused test after vtcombo was started.\n'
                'For manual testing, connect to vtctld: %s' % cls.vtctld_addr)

  @classmethod
  def tearDownClass(cls):
    cls.db.teardown()
    cls.driver.quit()

  
  # Navigation
  def _navigate_to_dashboard(self):
    logging.info('Fetching main vtctld page: %s', self.vtctld_addr)
    self.driver.get(self.vtctld_addr)
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.ID, 'test_keyspace')))

  def _navigate_to_keyspace_view(self):
    self._navigate_to_dashboard()
    dashboard_content = self.driver.find_element_by_tag_name('vt-dashboard')
    keyspace_cards = dashboard_content.find_elements_by_class_name('vt-card')
    self.assertEqual(2, len(keyspace_cards))

    first_keyspace_card = keyspace_cards[0]
    shard_stats = first_keyspace_card.find_element_by_tag_name('md-list')
    shard_stats.click()
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.CLASS_NAME, 'vt-card')))

  def _navigate_to_shard_view(self):
    self._navigate_to_keyspace_view()
    keyspace_content = self.driver.find_element_by_tag_name('vt-keyspace-view')
    shard_cards = keyspace_content.find_elements_by_class_name('vt-serving-shard')
    self.assertEqual(2, len(shard_cards))

    first_shard_card = shard_cards[0]
    first_shard_card.click()
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.ID, '1')))

  # Get Elements
  def _get_dashboard_keyspaces(self):
    """Get list of all present keyspaces."""
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.TAG_NAME, 'vt-dashboard')))
    dashboard_content = self.driver.find_element_by_tag_name('vt-dashboard')
    return [ks.text for ks in
            dashboard_content.find_elements_by_class_name('vt-keyspace-card')]

  def _get_dashboard_shards(self):
    """Get list of all present shards."""
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.TAG_NAME, 'vt-dashboard')))
    dashboard_content = self.driver.find_element_by_tag_name('vt-dashboard')
    return [sh.text for sh in
            dashboard_content.find_elements_by_class_name('vt-shard-stats')]

  def _get_keyspace_shards(self):
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.TAG_NAME, 'vt-keyspace-view')))
    keyspace_content = self.driver.find_element_by_tag_name('vt-keyspace-view')
    return [sh.text for sh in
            keyspace_content.find_elements_by_class_name('vt-serving-shard')]

  def _get_shard_tablets(self):
    wait = WebDriverWait(self.driver, 10)
    wait.until(expected_conditions.visibility_of_element_located(
        (By.TAG_NAME, 'vt-shard-view')))
    shard_content = self.driver.find_element_by_tag_name('vt-shard-view')
    
    # Ignore Header row.
    tablet_types = []
    tablet_uids = []
    table_rows = shard_content.find_elements_by_tag_name('tr')[1:]
    for row in table_rows:
      columns = row.find_elements_by_tag_name('td')
      tablet_types.append(columns[1].find_element_by_class_name('ui-cell-data').text)
      tablet_uids.append(columns[3].find_element_by_class_name('ui-cell-data').text)
    return (tablet_types, tablet_uids)

  def _get_first_option(self, dashboard_content):
    dashboard_menu = dashboard_content.find_element_by_class_name('vt-menu')
    dashboard_menu.click()
    first_option = dashboard_content.find_element_by_class_name('ui-menuitem-text')
    return first_option

  def _get_dialog_cmd(self, dialog):
    dialog_command = [cmd.text for cmd  in dialog.find_elements_by_class_name('vt-sheet')]
    return dialog_command

  def _toggle_dialog_checkbox(self, dialog, index):
    ping_tablets_checkbox = dialog.find_elements_by_class_name('md-checkbox-inner-container')[index]
    ping_tablets_checkbox.click()

  def _get_validate_resp(self, dialog):
    validate = dialog.find_element_by_id('vt-action')
    validate.click()
    validate_response = dialog.find_element_by_class_name('vt-resp').text
    return validate_response

  def _close_dialog(self, dialog):
    dismiss = dialog.find_element_by_id('vt-dismiss')
    dismiss.click()

  def test_dashboard(self):
    logging.info('Testing dashboard view')

    self._navigate_to_dashboard()

    keyspace_names = self._get_dashboard_keyspaces()
    shard_names = self._get_dashboard_shards()
    logging.info('Keyspaces: %s', ', '.join(keyspace_names))
    logging.info('Shards: %s', ', '.join(shard_names))
    self.assertListEqual(['test_keyspace', 'test_keyspace2'], keyspace_names)
    self.assertListEqual(['2 Shards', '1 Shards'], shard_names)

  def test_dashboard_validate(self):
    self._navigate_to_dashboard()
    dashboard_content = self.driver.find_element_by_tag_name('vt-dashboard')
    first_menu_option = self._get_first_option(dashboard_content)
    logging.info('First option of Dashboard menu: %s', first_menu_option.text)
    self.assertEqual('Validate', first_menu_option.text)

    first_menu_option.click()
    dialog = dashboard_content.find_element_by_tag_name('vt-dialog')
    dialog_command = self._get_dialog_cmd(dialog)
    logging.info('Validate command: %s', ', '.join(dialog_command))
    self.assertEqual(1, len(dialog_command))
    self.assertListEqual(['Validate'], dialog_command)
    
    # Validate Dialog Checkbox is working
    self._toggle_dialog_checkbox(dialog, 0)
    dialog_command = self._get_dialog_cmd(dialog)
    logging.info('Validate command: %s', ', '.join(dialog_command))
    self.assertEqual(2, len(dialog_command))
    self.assertEqual('-ping-tablets=true', dialog_command[1])

    # Validate succeeded
    validate_response = self._get_validate_resp(dialog)
    logging.info('Validate command response: %s', validate_response)
    self._close_dialog(dialog)

  def test_create_keyspace(self):
    self._navigate_to_dashboard()
    dashboard_content = self.driver.find_element_by_tag_name('vt-dashboard')
    dialog = dashboard_content.find_element_by_tag_name('vt-dialog')
    # Create Keyspace Dialog command responds to name.
    add_button = dashboard_content.find_element_by_class_name('add-button')
    add_button.click()
    input_fields = [md_input.find_element_by_tag_name('input') for md_input in dialog.find_elements_by_tag_name('md-input')]
    keyspace_name_field = input_fields[0]
    sharding_col_name_field = input_fields[1]
    keyspace_name_field.send_keys('test_keyspace3')
    dialog_command = [cmd.text for cmd  in dialog.find_elements_by_class_name('vt-sheet')]
    logging.info('Create keyspace command: %s', ', '.join(dialog_command))
    self.assertEqual(2, len(dialog_command))
    self.assertListEqual(['CreateKeyspace', 'test_keyspace3'], dialog_command)

    # Create Keyspace autopopulates sharding_column type
    sharding_col_name_field.send_keys('test_id')
    dialog_command = [cmd.text for cmd  in dialog.find_elements_by_class_name('vt-sheet')]
    logging.info('Create keyspace command: %s', ', '.join(dialog_command))
    self.assertEqual(4, len(dialog_command))
    self.assertListEqual(['CreateKeyspace', '-sharding_column_name=test_id', '-sharding_column_type=UINT64', 'test_keyspace3'], dialog_command)
    
    # Dropdown works
    dropdown = dialog.find_element_by_tag_name('p-dropdown')
    dropdown.click()
    options = dropdown.find_elements_by_tag_name('li')
    options[1].click()
    dialog_command = [cmd.text for cmd  in dialog.find_elements_by_class_name('vt-sheet')]
    logging.info('Create keyspace command: %s', ', '.join(dialog_command))
    self.assertEqual(4, len(dialog_command))
    self.assertListEqual(['CreateKeyspace', '-sharding_column_name=test_id', '-sharding_column_type=BYTES', 'test_keyspace3'], dialog_command)

    create = dialog.find_element_by_id('vt-action')
    create.click()

    dismiss = dialog.find_element_by_id('vt-dismiss')
    dismiss.click()

    keyspace_names = self._get_dashboard_keyspaces()
    logging.info('Keyspaces: %s', ', '.join(keyspace_names))
    self.assertListEqual(['test_keyspace', 'test_keyspace2', 'test_keyspace3'], keyspace_names)

    test_keyspace3 = dashboard_content.find_elements_by_class_name('vt-card')[2]
    test_keyspace3.find_element_by_class_name('vt-menu').click()
    options = test_keyspace3.find_elements_by_tag_name('li')

    edit = options[0]
    delete = options[1]
    delete.click()

    delete = dialog.find_element_by_id('vt-action')
    delete.click()
    dismiss = dialog.find_element_by_id('vt-dismiss')
    dismiss.click()
    keyspace_names = self._get_dashboard_keyspaces()
    logging.info('Keyspaces: %s', ', '.join(keyspace_names))
    self.assertListEqual(['test_keyspace', 'test_keyspace2'], keyspace_names)
    
  def test_keyspace_view(self):
    self._navigate_to_keyspace_view()
    logging.info('Navigating to keyspace view')
    self._navigate_to_keyspace_view()
    logging.info('Testing keyspace view')
    shard_names = self._get_keyspace_shards();
    logging.info('Shards in first keyspace: %s', ', '.join(shard_names))
    self.assertListEqual(['-80', '80-'], shard_names)

  def test_shard_view(self):
    self._navigate_to_shard_view()
    logging.info('Navigating to shard view')
    self._navigate_to_shard_view()
    logging.info('Testing shard view')
    tablet_types, tablet_uids = self._get_shard_tablets()
    logging.info('Tablets types in first shard in first keyspace: %s', ', '.join(tablet_types))
    logging.info('Tablets uids in first shard in first keyspace: %s', ', '.join(tablet_uids))
    self.assertListEqual(['master', 'replica', 'rdonly', 'rdonly'], tablet_types)
    self.assertListEqual(['1', '2', '3', '4'], tablet_uids)


def add_test_options(parser):
  parser.add_option(
      '--no-xvfb', action='store_false', dest='xvfb', default=True,
      help='Use local DISPLAY instead of headless Xvfb mode.')


if __name__ == '__main__':
  utils.main(test_options=add_test_options)
