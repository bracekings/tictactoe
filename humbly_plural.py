"""
Humbly Plural - A comprehensive plural system management app
A free, open-source replica of Simply Plural for managing DID/OSDD systems
"""

import json
import os
from datetime import datetime, timedelta
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, ListProperty, ObjectProperty


class Member:
    """Represents a system member/alter"""
    def __init__(self, name, pronouns="", description="", avatar_path="", role="", color="#FFFFFF"):
        self.id = str(datetime.now().timestamp())
        self.name = name
        self.pronouns = pronouns
        self.description = description
        self.avatar_path = avatar_path
        self.role = role
        self.color = color
        self.created_date = datetime.now().isoformat()
        self.last_fronted = None

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'pronouns': self.pronouns,
            'description': self.description,
            'avatar_path': self.avatar_path,
            'role': self.role,
            'color': self.color,
            'created_date': self.created_date,
            'last_fronted': self.last_fronted
        }

    @classmethod
    def from_dict(cls, data):
        member = cls(
            data['name'],
            data.get('pronouns', ''),
            data.get('description', ''),
            data.get('avatar_path', ''),
            data.get('role', ''),
            data.get('color', '#FFFFFF')
        )
        member.id = data['id']
        member.created_date = data.get('created_date', datetime.now().isoformat())
        member.last_fronted = data.get('last_fronted')
        return member


class Switch:
    """Represents a fronting switch"""
    def __init__(self, member_ids, start_time=None, end_time=None, notes=""):
        self.id = str(datetime.now().timestamp())
        self.member_ids = member_ids if isinstance(member_ids, list) else [member_ids]
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.notes = notes

    def to_dict(self):
        return {
            'id': self.id,
            'member_ids': self.member_ids,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data):
        switch = cls(
            data['member_ids'],
            datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            data.get('notes', '')
        )
        switch.id = data['id']
        return switch


class Note:
    """Represents a journal note"""
    def __init__(self, title, content, member_ids=None, tags=None, timestamp=None):
        self.id = str(datetime.now().timestamp())
        self.title = title
        self.content = content
        self.member_ids = member_ids or []
        self.tags = tags or []
        self.timestamp = timestamp or datetime.now()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'member_ids': self.member_ids,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        note = cls(
            data['title'],
            data['content'],
            data.get('member_ids', []),
            data.get('tags', []),
            datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        )
        note.id = data['id']
        return note


class DataManager:
    """Manages data persistence"""
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.members_file = os.path.join(data_dir, "members.json")
        self.switches_file = os.path.join(data_dir, "switches.json")
        self.notes_file = os.path.join(data_dir, "notes.json")
        self.settings_file = os.path.join(data_dir, "settings.json")

        os.makedirs(data_dir, exist_ok=True)

        self.members = self.load_members()
        self.switches = self.load_switches()
        self.notes = self.load_notes()
        self.settings = self.load_settings()

    def load_members(self):
        if os.path.exists(self.members_file):
            with open(self.members_file, 'r') as f:
                data = json.load(f)
                return [Member.from_dict(m) for m in data]
        return []

    def save_members(self):
        with open(self.members_file, 'w') as f:
            json.dump([m.to_dict() for m in self.members], f, indent=2)

    def load_switches(self):
        if os.path.exists(self.switches_file):
            with open(self.switches_file, 'r') as f:
                data = json.load(f)
                return [Switch.from_dict(s) for s in data]
        return []

    def save_switches(self):
        with open(self.switches_file, 'w') as f:
            json.dump([s.to_dict() for s in self.switches], f, indent=2)

    def load_notes(self):
        if os.path.exists(self.notes_file):
            with open(self.notes_file, 'r') as f:
                data = json.load(f)
                return [Note.from_dict(n) for n in data]
        return []

    def save_notes(self):
        with open(self.notes_file, 'w') as f:
            json.dump([n.to_dict() for n in self.notes], f, indent=2)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        return {
            'theme': 'light',
            'auto_backup': True,
            'reminders': True,
            'current_front': None
        }

    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)


class MemberCard(BoxLayout):
    """Widget to display a member card"""
    def __init__(self, member, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(10)
        self.spacing = dp(5)

        # Avatar and name
        top_layout = BoxLayout(size_hint_y=None, height=dp(60))
        self.avatar = Image(
            source=member.avatar_path if member.avatar_path else 'default_avatar.png',
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            pos_hint={'center_y': 0.5}
        )
        top_layout.add_widget(self.avatar)

        name_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        self.name_label = Label(
            text=member.name,
            font_size=dp(18),
            bold=True,
            halign='left',
            valign='middle'
        )
        self.name_label.bind(size=self.name_label.setter('text_size'))
        name_layout.add_widget(self.name_label)

        if member.pronouns:
            self.pronouns_label = Label(
                text=member.pronouns,
                font_size=dp(12),
                color=(0.7, 0.7, 0.7, 1),
                halign='left'
            )
            self.pronouns_label.bind(size=self.pronouns_label.setter('text_size'))
            name_layout.add_widget(self.pronouns_label)

        top_layout.add_widget(name_layout)
        self.add_widget(top_layout)

        # Role and description
        if member.role:
            self.role_label = Label(
                text=f"Role: {member.role}",
                font_size=dp(12),
                halign='left',
                size_hint_y=None,
                height=dp(20)
            )
            self.role_label.bind(size=self.role_label.setter('text_size'))
            self.add_widget(self.role_label)

        if member.description:
            self.desc_label = Label(
                text=member.description[:50] + "..." if len(member.description) > 50 else member.description,
                font_size=dp(12),
                halign='left',
                size_hint_y=None,
                height=dp(30)
            )
            self.desc_label.bind(size=self.desc_label.setter('text_size'))
            self.add_widget(self.desc_label)


class MembersScreen(Screen):
    """Screen for managing system members"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.layout = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(10))
        header.add_widget(Label(text="System Members", font_size=dp(24), bold=True))

        add_btn = Button(text="+ Add Member", size_hint_x=None, width=dp(120))
        add_btn.bind(on_press=self.add_member)
        header.add_widget(add_btn)
        self.layout.add_widget(header)

        # Members list
        self.scroll_view = ScrollView()
        self.members_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.members_layout.bind(minimum_height=self.members_layout.setter('height'))
        self.scroll_view.add_widget(self.members_layout)
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)
        self.refresh_members()

    def refresh_members(self):
        self.members_layout.clear_widgets()
        for member in self.data_manager.members:
            card = MemberCard(member)
            btn = Button(background_normal='', background_color=(0, 0, 0, 0))
            btn.add_widget(card)
            btn.bind(on_press=lambda x, m=member: self.edit_member(m))
            self.members_layout.add_widget(btn)

    def add_member(self, instance):
        self.manager.current = 'add_edit_member'

    def edit_member(self, member):
        self.manager.get_screen('add_edit_member').load_member(member)
        self.manager.current = 'add_edit_member'


class AddEditMemberScreen(Screen):
    """Screen for adding or editing a member"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.current_member = None

        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # Header
        self.header = Label(text="Add Member", font_size=dp(24), bold=True, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.header)

        # Form fields
        self.name_input = TextInput(hint_text="Name", multiline=False, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.name_input)

        self.pronouns_input = TextInput(hint_text="Pronouns (e.g., they/them)", multiline=False, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.pronouns_input)

        self.role_input = TextInput(hint_text="Role (e.g., protector, host)", multiline=False, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.role_input)

        self.desc_input = TextInput(hint_text="Description", multiline=True, size_hint_y=None, height=dp(100))
        self.layout.add_widget(self.desc_input)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.cancel)
        btn_layout.add_widget(cancel_btn)

        save_btn = Button(text="Save")
        save_btn.bind(on_press=self.save)
        btn_layout.add_widget(save_btn)

        self.layout.add_widget(btn_layout)
        self.add_widget(self.layout)

    def load_member(self, member=None):
        self.current_member = member
        if member:
            self.header.text = "Edit Member"
            self.name_input.text = member.name
            self.pronouns_input.text = member.pronouns
            self.role_input.text = member.role
            self.desc_input.text = member.description
        else:
            self.header.text = "Add Member"
            self.name_input.text = ""
            self.pronouns_input.text = ""
            self.role_input.text = ""
            self.desc_input.text = ""

    def save(self, instance):
        if not self.name_input.text.strip():
            return  # Require name

        if self.current_member:
            self.current_member.name = self.name_input.text.strip()
            self.current_member.pronouns = self.pronouns_input.text.strip()
            self.current_member.role = self.role_input.text.strip()
            self.current_member.description = self.desc_input.text.strip()
        else:
            member = Member(
                self.name_input.text.strip(),
                self.pronouns_input.text.strip(),
                self.desc_input.text.strip(),
                "",
                self.role_input.text.strip()
            )
            self.data_manager.members.append(member)

        self.data_manager.save_members()
        self.manager.get_screen('members').refresh_members()
        self.cancel(instance)

    def cancel(self, instance):
        self.manager.current = 'members'


class FrontingScreen(Screen):
    """Screen for tracking who's currently fronting"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.current_switch = None
        self.selected_members = []
        self.member_buttons = {}

        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # Header
        self.header = Label(text="Who's Fronting?", font_size=dp(24), bold=True, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.header)

        # Current front status
        self.status_label = Label(text="No one currently marked as fronting", size_hint_y=None, height=dp(30))
        self.layout.add_widget(self.status_label)

        # Members list for selection
        self.scroll_view = ScrollView()
        self.members_layout = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        self.members_layout.bind(minimum_height=self.members_layout.setter('height'))
        self.scroll_view.add_widget(self.members_layout)
        self.layout.add_widget(self.scroll_view)

        # Notes for switch
        self.notes_input = TextInput(hint_text="Notes about this switch", multiline=True, size_hint_y=None, height=dp(80))
        self.layout.add_widget(self.notes_input)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.start_btn = Button(text="Start Switch")
        self.start_btn.bind(on_press=self.start_switch)
        btn_layout.add_widget(self.start_btn)

        self.end_btn = Button(text="End Switch", disabled=True)
        self.end_btn.bind(on_press=self.end_switch)
        btn_layout.add_widget(self.end_btn)

        self.layout.add_widget(btn_layout)
        self.add_widget(self.layout)
        self.refresh_members()

    def refresh_members(self):
        self.members_layout.clear_widgets()
        self.member_buttons.clear()
        for member in self.data_manager.members:
            btn = Button(text=member.name, size_hint_y=None, height=dp(50))
            btn.bind(on_press=lambda x, m=member: self.select_member(m))
            self.members_layout.add_widget(btn)
            self.member_buttons[member.id] = btn

        # Add co-fronting option
        cofront_btn = Button(text="+ Co-fronting", size_hint_y=None, height=dp(50))
        cofront_btn.bind(on_press=self.select_cofronting)
        self.members_layout.add_widget(cofront_btn)

    def select_member(self, member):
        # Toggle selection
        if hasattr(self, 'selected_members'):
            if member in self.selected_members:
                self.selected_members.remove(member)
            else:
                self.selected_members.append(member)
        else:
            self.selected_members = [member]

        self.update_selection_display()

    def select_cofronting(self, instance):
        # For co-fronting, allow multiple selections and show instructions
        self.status_label.text = "Co-fronting mode: tap multiple members, then tap Start Switch."
        self.update_selection_display()

    def update_selection_display(self):
        if self.selected_members:
            names = [m.name for m in self.selected_members]
            self.status_label.text = f"Selected: {', '.join(names)}"
        else:
            self.status_label.text = "Tap a member to select who is fronting"

        for member_id, btn in self.member_buttons.items():
            if any(m.id == member_id for m in self.selected_members):
                btn.background_color = (0.2, 0.6, 0.9, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (1, 1, 1, 1)
                btn.color = (0, 0, 0, 1)

    def start_switch(self, instance):
        if not self.selected_members:
            self.status_label.text = "Select at least one member before starting a switch."
            return

        # End any current switch
        if self.current_switch:
            self.end_switch(instance)

        self.current_switch = Switch(
            [m.id for m in self.selected_members],
            notes=self.notes_input.text
        )
        self.data_manager.switches.append(self.current_switch)
        self.data_manager.save_switches()

        self.status_label.text = f"Currently fronting: {', '.join([m.name for m in self.selected_members])}"
        self.start_btn.disabled = True
        self.end_btn.disabled = False
        self.notes_input.text = ""

    def end_switch(self, instance):
        if self.current_switch:
            self.current_switch.end_time = datetime.now()
            self.data_manager.save_switches()
            self.current_switch = None

        self.status_label.text = "Switch ended"
        self.start_btn.disabled = False
        self.end_btn.disabled = True


class NotesScreen(Screen):
    """Screen for journal/notes"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager

        self.layout = BoxLayout(orientation='vertical')

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(10))
        header.add_widget(Label(text="Journal", font_size=dp(24), bold=True))

        add_btn = Button(text="+ New Note", size_hint_x=None, width=dp(120))
        add_btn.bind(on_press=self.add_note)
        header.add_widget(add_btn)
        self.layout.add_widget(header)

        # Notes list
        self.scroll_view = ScrollView()
        self.notes_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        self.notes_layout.bind(minimum_height=self.notes_layout.setter('height'))
        self.scroll_view.add_widget(self.notes_layout)
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)
        self.refresh_notes()

    def refresh_notes(self):
        self.notes_layout.clear_widgets()
        for note in sorted(self.data_manager.notes, key=lambda x: x.timestamp, reverse=True):
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80), padding=dp(10))
            card.add_widget(Label(text=note.title, font_size=dp(16), bold=True))
            card.add_widget(Label(text=note.timestamp.strftime("%Y-%m-%d %H:%M"), font_size=dp(12), color=(0.5, 0.5, 0.5, 1)))
            preview = note.content[:100] + "..." if len(note.content) > 100 else note.content
            card.add_widget(Label(text=preview, font_size=dp(12)))

            btn = Button(background_normal='', background_color=(0, 0, 0, 0))
            btn.add_widget(card)
            btn.bind(on_press=lambda x, n=note: self.view_note(n))
            self.notes_layout.add_widget(btn)

    def add_note(self, instance):
        self.manager.current = 'add_edit_note'

    def view_note(self, note):
        self.manager.get_screen('add_edit_note').load_note(note)
        self.manager.current = 'add_edit_note'


class AddEditNoteScreen(Screen):
    """Screen for adding or editing notes"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager
        self.current_note = None

        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        # Header
        self.header = Label(text="New Note", font_size=dp(24), bold=True, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.header)

        # Form fields
        self.title_input = TextInput(hint_text="Title", multiline=False, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.title_input)

        self.content_input = TextInput(hint_text="Content", multiline=True, size_hint_y=None, height=dp(200))
        self.layout.add_widget(self.content_input)

        # Buttons
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel_btn = Button(text="Cancel")
        cancel_btn.bind(on_press=self.cancel)
        btn_layout.add_widget(cancel_btn)

        save_btn = Button(text="Save")
        save_btn.bind(on_press=self.save)
        btn_layout.add_widget(save_btn)

        self.layout.add_widget(btn_layout)
        self.add_widget(self.layout)

    def load_note(self, note=None):
        self.current_note = note
        if note:
            self.header.text = "Edit Note"
            self.title_input.text = note.title
            self.content_input.text = note.content
        else:
            self.header.text = "New Note"
            self.title_input.text = ""
            self.content_input.text = ""

    def save(self, instance):
        if not self.title_input.text.strip():
            return

        if self.current_note:
            self.current_note.title = self.title_input.text.strip()
            self.current_note.content = self.content_input.text.strip()
            self.current_note.timestamp = datetime.now()
        else:
            note = Note(
                self.title_input.text.strip(),
                self.content_input.text.strip()
            )
            self.data_manager.notes.append(note)

        self.data_manager.save_notes()
        self.manager.get_screen('notes').refresh_notes()
        self.cancel(instance)

    def cancel(self, instance):
        self.manager.current = 'notes'


class StatsScreen(Screen):
    """Screen for viewing statistics"""
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.data_manager = data_manager

        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        self.header = Label(text="Statistics", font_size=dp(24), bold=True, size_hint_y=None, height=dp(40))
        self.layout.add_widget(self.header)

        # Stats content
        self.stats_layout = BoxLayout(orientation='vertical', spacing=dp(15))
        self.layout.add_widget(self.stats_layout)

        self.add_widget(self.layout)
        self.refresh_stats()

    def refresh_stats(self):
        self.stats_layout.clear_widgets()

        # Member count
        member_count = len(self.data_manager.members)
        self.stats_layout.add_widget(Label(text=f"Total Members: {member_count}", font_size=dp(16)))

        # Switch count
        switch_count = len(self.data_manager.switches)
        self.stats_layout.add_widget(Label(text=f"Total Switches: {switch_count}", font_size=dp(16)))

        # Notes count
        notes_count = len(self.data_manager.notes)
        self.stats_layout.add_widget(Label(text=f"Total Notes: {notes_count}", font_size=dp(16)))

        # Recent activity
        if self.data_manager.switches:
            last_switch = max(self.data_manager.switches, key=lambda x: x.start_time)
            self.stats_layout.add_widget(Label(
                text=f"Last Switch: {last_switch.start_time.strftime('%Y-%m-%d %H:%M')}",
                font_size=dp(16)
            ))

        # Most active members
        if self.data_manager.switches:
            member_switch_counts = {}
            for switch in self.data_manager.switches:
                for member_id in switch.member_ids:
                    member_switch_counts[member_id] = member_switch_counts.get(member_id, 0) + 1

            if member_switch_counts:
                most_active_id = max(member_switch_counts, key=member_switch_counts.get)
                most_active_member = next((m for m in self.data_manager.members if m.id == most_active_id), None)
                if most_active_member:
                    self.stats_layout.add_widget(Label(
                        text=f"Most Active: {most_active_member.name} ({member_switch_counts[most_active_id]} switches)",
                        font_size=dp(16)
                    ))


class HumblyPluralApp(App):
    """Main application class"""
    def build(self):
        self.data_manager = DataManager()

        # Set up screen manager
        self.sm = ScreenManager()

        # Create screens
        self.members_screen = MembersScreen(self.data_manager, name='members')
        self.add_edit_member_screen = AddEditMemberScreen(self.data_manager, name='add_edit_member')
        self.fronting_screen = FrontingScreen(self.data_manager, name='fronting')
        self.notes_screen = NotesScreen(self.data_manager, name='notes')
        self.add_edit_note_screen = AddEditNoteScreen(self.data_manager, name='add_edit_note')
        self.stats_screen = StatsScreen(self.data_manager, name='stats')

        # Add screens to manager
        self.sm.add_widget(self.members_screen)
        self.sm.add_widget(self.add_edit_member_screen)
        self.sm.add_widget(self.fronting_screen)
        self.sm.add_widget(self.notes_screen)
        self.sm.add_widget(self.add_edit_note_screen)
        self.sm.add_widget(self.stats_screen)

        # Create main navigation
        main_layout = BoxLayout(orientation='vertical')

        # Navigation tabs
        self.tabs = TabbedPanel(do_default_tab=False)

        members_tab = TabbedPanelItem(text='Members')
        members_tab.add_widget(self.sm)
        self.tabs.add_widget(members_tab)

        fronting_tab = TabbedPanelItem(text='Fronting')
        fronting_tab.add_widget(self.sm)
        self.tabs.add_widget(fronting_tab)

        notes_tab = TabbedPanelItem(text='Journal')
        notes_tab.add_widget(self.sm)
        self.tabs.add_widget(notes_tab)

        stats_tab = TabbedPanelItem(text='Stats')
        stats_tab.add_widget(self.sm)
        self.tabs.add_widget(stats_tab)

        # Set default screen
        self.sm.current = 'members'
        self.tabs.switch_to(members_tab)

        # Bind tab changes to screen changes
        self.tabs.bind(current_tab=self.on_tab_change)

        main_layout.add_widget(self.tabs)
        return main_layout

    def on_tab_change(self, instance, tab):
        if tab.text == 'Members':
            self.sm.current = 'members'
        elif tab.text == 'Fronting':
            self.sm.current = 'fronting'
        elif tab.text == 'Journal':
            self.sm.current = 'notes'
        elif tab.text == 'Stats':
            self.sm.current = 'stats'

    def on_stop(self):
        # Save data on exit
        self.data_manager.save_members()
        self.data_manager.save_switches()
        self.data_manager.save_notes()
        self.data_manager.save_settings()


if __name__ == '__main__':
    HumblyPluralApp().run()