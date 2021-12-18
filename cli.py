import sys
from time import sleep

from notion.client import NotionClient
from notion.block import PageBlock
from notion.operations import build_operation

from tqdm import tqdm

DEFAULT_SETTING = 'true'
DEFAULT_DELAY = 0.5

DISALLOWED_ACCESS_ERRORS = [
    'User does not have edit access to record',
    'Not allowed to edit column: format',
]

class FullWidthSetterClient:
    def __init__(self, email, password=None, token_v2=None):
        self.email = email

        self.notion = NotionClient(
            email=email,
            password=password,
            token_v2=token_v2,
            monitor=False
        )

    def fetch_spaces(self):
        """
        Fetches the list of workspaces that the user is NOT a guest in.
        """

        email_uid = self.notion.get_email_uid()[self.email]

        spaces_json = self.notion.post("getSpaces", {}).json()
        space_ids = list(spaces_json[email_uid]['space'].keys())
        spaces = [self.notion.get_space(space_id) for space_id in space_ids]
        return spaces


    def _prompt_for_single_space(self, spaces):
        """
        When presented with multiple workspaces to select, prompt the user for the intended workspace.
        """

        selected_index = -1

        while True:
            print('Select the intended workspace:')
            for (i, space) in enumerate(spaces):
                print(f' {i + 1}) {space.name}')
            selected_index = int(input('Input: ')) - 1

            if selected_index >= 0 and selected_index < len(spaces):
                break
            else:
                print('Invalid input, please try again')
                print()

        # NOTE: Added extra newline to make output a bit more clean
        print()

        return spaces[selected_index]


    def fetch_single_space(self):
        """
        Fetches a single workspace, prompting the user if they are part of multiple workspaces.
        """

        spaces = self.fetch_spaces()

        if len(spaces) > 1:
            selected_space = self._prompt_for_single_space(spaces)
        else:
            selected_space = spaces[0]

        return selected_space


    def _fetch_pages_recursively(self, page):
        """
        Iterates through a page's children and dives into the child pages.
        """

        pages = []

        for child in page.children:
            if type(child) == PageBlock:
                pages += [child]
                pages += self._fetch_pages_recursively(child)

        return pages


    def fetch_pages_in_space(self, space, delay=DEFAULT_DELAY):
        """
        Fetches all pages within a workspace.
        """

        # First fetch all top level pages
        root_pages = self.notion.get_top_level_pages()

        # Then iterate through the tree hiearchy of pages from those root pages
        all_pages = root_pages
        for root_page in root_pages:
            all_pages += self._fetch_pages_recursively(root_page)

        all_unique_pages = list(set(all_pages))
        return all_unique_pages


    # Source: https://github.com/jamalex/notion-py/pull/284
    def set_full_width_on_page(self, page_id, full_width):
        """
        Sets the full width setting for the selected page.
        """

        args = {"page_full_width": full_width}

        try:
            self.notion.submit_transaction(
                [build_operation(
                    id=page_id, path=["format"], args=args, command="update"
                )]
            )

            return True
        except Exception as ex:
            msg = str(ex)
            for possible_error in DISALLOWED_ACCESS_ERRORS:
                if possible_error in msg:
                    # The user cannot edit the page so we'll ignore it
                    return False

            # Throw for any other type of error
            raise ex

if __name__ == '__main__':
    # Process arguments
    args = dict(enumerate(sys.argv))

    email = args.get(1)
    if email is None:
        raise Exception('Email is required')

    full_width = args.get(2, DEFAULT_SETTING).lower()
    if full_width == 'true':
        full_width = True
    elif full_width == 'false':
        full_width = False
    else:
        raise Exception('Full width setting must be "true" or "false"')

    # NOTE: This shouldn't need to be changed
    rate_limit_delay = args.get(3, DEFAULT_DELAY)
    try:
        rate_limit_delay = float(rate_limit_delay)
    except:
        raise Exception('Delay must be a number in seconds')

    # Initialize Notion client
    client = FullWidthSetterClient(email=email)

    # Fetch all pages that will be altered
    target_space = client.fetch_single_space()
    
    print('Fetching all pages to iterate through...')
    target_pages = client.fetch_pages_in_space(target_space, rate_limit_delay)

    # Process through all the pages
    pbar = tqdm(target_pages)
    total = len(target_pages)
    failed = 0

    for page in pbar:
        pbar.set_description("Processing pages")
        success = client.set_full_width_on_page(page.id, full_width)

        if not success:
            failed += 1

        # Respect the rate limit rules for Notion (not sure if they apply for internal API)
        # Source: https://developers.notion.com/reference/errors#rate-limits
        sleep(rate_limit_delay)

    print(f'Successfully altered {total - failed} out of {total} pages!')
