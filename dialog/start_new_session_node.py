# pylint: disable=line-too-long, super-with-arguments, no-member, cyclic-import

import json

from django_dialog_engine.dialog.base_node import BaseNode, DialogTransition, fetch_default_logger

class StartNewSessionNode(BaseNode):
    @staticmethod
    def parse(dialog_def):
        if dialog_def['type'] == 'start-new-session':
            return StartNewSessionNode(dialog_def['id'], dialog_def.get('script_id', None))

        return None

    def __init__(self, node_id, script_id):# pylint: disable=too-many-arguments
        super(StartNewSessionNode, self).__init__(node_id, None) # pylint: disable=super-with-arguments

        self.script_id = script_id

    def node_type(self):
        return 'start-new-session'

    def str(self):
        return json.dumps(self.node_definition(), indent=2)

    def evaluate(self, dialog, response=None, last_transition=None, extras=None, logger=None): # pylint: disable=too-many-arguments
        if extras is None:
            extras = {}

        if logger is None:
            logger = fetch_default_logger()

        transition = DialogTransition(new_state_id=None)

        transition.metadata['reason'] = 'start-new-session'
        transition.metadata['new_session_script'] = self.script_id

        transition.metadata['exit_actions'] = [{
            'type': 'start-new-session',
            'script_id': self.script_id
        }]

        return transition

    def actions(self):
        return []

    def next_nodes(self):
        return []

    def node_definition(self):
        node_def = super().node_definition() # pylint: disable=missing-super-argument

        node_def['script_id'] = self.script_id

        if 'next_id' in node_def:
            del node_def['next_id']

        return node_def
