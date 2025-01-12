import os

from postProcessing.PostProcessor import PostProcessor


class ExternalClientsRelativePathProcessor(PostProcessor):

    def perform_post_process(self) -> None:
        processed_files = []
        skipped_files = []
        ignored_files = []

        import_statements_to_replace = [
            "import common_pb2",
            "import users_pb2"
        ]

        generated_dir = "externalClients/TInvestApi/proto"

        for root, _, files in os.walk(generated_dir):
            for file in files:
                filepath = os.path.join(root, file)

                if not file.endswith(".py"):
                    ignored_files.append(file)
                    continue

                with open(filepath, "r", encoding='UTF-8') as f:
                    content = f.read()

                file_modified: bool = False
                for import_statement in import_statements_to_replace:
                    fix_import_result = ExternalClientsRelativePathProcessor.fix_import(content, import_statement)
                    file_modified |= fix_import_result[0]
                    content = fix_import_result[1]

                if not file_modified:
                    skipped_files.append(file)
                    continue

                with open(filepath, "w", encoding='UTF-8') as f:
                    f.write(content)
                    processed_files.append(file)

        print(f'''
        processed: {processed_files}
        skipped: {skipped_files}
        ignored: {ignored_files}
        ''')

    @staticmethod
    def fix_import(file_content: str, import_statement: str) -> (bool, str):
        if (import_statement not in file_content or
                f'from externalClients.TInvestApi.proto {import_statement}' in file_content):
            return False, file_content

        modified_content = file_content.replace(
            import_statement, f"from externalClients.TInvestApi.proto {import_statement}")
        return True, modified_content
