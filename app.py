import streamlit as st
from streamlit.hashing import _CodeHasher
from streamlit.report_thread import get_report_ctx
from streamlit.server.server import Server
from daily_transactions import daily_transactions
from sells_analysis import sells_analysis
from data_repository import retrieve_db_data
from hashlib import sha256

HASHED_USERNAME = '4cf6829aa93728e8f3c97df913fb1bfa95fe5810e2933a05943f8312a98d9cf2'
HASHED_PASSWORD = '6a64d9bb83648ab83c4c5ee7434056a186ac6475454107501991cd9912834140'
GLOBAL_PASSWORD = 'f276e34a3ec53f1e46c0c9514958aca2855abca97db9c92079f67eb402e992d9'


def valid_credentials(credentials):
    global HASHED_USERNAME, HASHED_PASSWORD, GLOBAL_PASSWORD
    hashed_username = sha256(credentials[0].strip().encode('utf-8')).hexdigest()
    hashed_password = sha256(credentials[1].strip().encode('utf-8')).hexdigest()
    hashed_password_2 = sha256(credentials[2].strip().encode('utf-8')).hexdigest()

    if hashed_username == HASHED_USERNAME \
            and hashed_password == HASHED_PASSWORD\
            and hashed_password_2 == GLOBAL_PASSWORD:
        return True
    return False


def main():
    state = _get_state()

    curr_credentials = state['credentials']

    if curr_credentials is None:
        curr_credentials = '', '', ''

    if not valid_credentials(curr_credentials):
        credentials(state)
    else:
        data = retrieve_db_data(username=curr_credentials[0], password=curr_credentials[1])
        if data.shape[0] > 0:
            state.user_is_logged = True

        page = st.sidebar.selectbox(
            "Извештаи",
            ("Дневни трансакции", "Анализа на продажби")
        )

        if page == 'Анализа на продажби':
            sells_analysis(data)
        elif page == 'Дневни трансакции':
            daily_transactions(data)


    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


def credentials(state):
    st.title('Најавување')

    st.text('Корисник')
    account = st.text_input('', key='account')

    st.text('Лозинка')
    password = st.text_input('', key='password')

    st.text('Лозинка 2')
    password_2 = st.text_input('', key='password_2')

    state['credentials'] = (account, password, password_2)


def page_dashboard(state):
    st.title(":chart_with_upwards_trend: Dashboard page")
    display_state_values(state)


def page_settings(state):
    st.title(":wrench: Settings")
    display_state_values(state)

    st.write("---")
    options = ["Hello", "World", "Goodbye"]
    state.input = st.text_input("Set input value.", state.input or "")
    state.slider = st.slider("Set slider value.", 1, 10, state.slider)
    state.radio = st.radio("Set radio value.", options, options.index(state.radio) if state.radio else 0)
    state.checkbox = st.checkbox("Set checkbox value.", state.checkbox)
    state.selectbox = st.selectbox("Select value.", options, options.index(state.selectbox) if state.selectbox else 0)
    state.multiselect = st.multiselect("Select value(s).", options, state.multiselect)

    # Dynamic state assignments
    for i in range(3):
        key = f"State value {i}"
        state[key] = st.slider(f"Set value {i}", 1, 10, state[key])


def display_state_values(state):
    st.write("Input state:", state.input)
    st.write("Slider state:", state.slider)
    st.write("Radio state:", state.radio)
    st.write("Checkbox state:", state.checkbox)
    st.write("Selectbox state:", state.selectbox)
    st.write("Multiselect state:", state.multiselect)

    for i in range(3):
        st.write(f"Value {i}:", state[f"State value {i}"])

    if st.button("Clear state"):
        state.clear()


class _SessionState:

    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self._state["session"].request_rerun()

    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False

        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)


def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")

    return session_info.session


def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state


if __name__ == "__main__":
    main()
