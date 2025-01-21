import os

from postProcessing.PostProcessor import PostProcessor
from postProcessing.RunResult import RunResult


class ProtoProcessorBase(PostProcessor):
    def __init__(self,
                 import_statements_to_replace: list[str],
                 files_dir: str,
                 new_prefix: str):
        self.import_statements_to_replace = import_statements_to_replace
        self.files_dir = files_dir
        self.new_prefix = new_prefix


    # noinspection PyBroadException
    def perform_post_process(self) -> None:
        if self.processor_name is not None:
            print(f"Running {self.processor_name}...")

        try:
            self.__perform_post_process_internal()
            self.log_result(RunResult.OK)
        except:
            self.log_result(RunResult.FAIL)


    def __perform_post_process_internal(self) -> None:


        processed_files = []
        skipped_files = []
        ignored_files = []

        for root, _, files in os.walk(self.files_dir):
            for file in files:
                filepath = os.path.join(root, file)

                if not file.endswith(".py"):
                    ignored_files.append(file)
                    continue

                with open(filepath, "r", encoding='UTF-8') as f:
                    content = f.read()

                file_modified: bool = False
                for import_statement in self.import_statements_to_replace:
                    fix_import_result = self.fix_import(content, import_statement)
                    file_modified |= fix_import_result[0]
                    content = fix_import_result[1]

                if not file_modified:
                    skipped_files.append(file)
                    continue

                with open(filepath, "w", encoding='UTF-8') as f:
                    f.write(content)
                    processed_files.append(file)

        print(f'''  processed: {processed_files}
    skipped: {skipped_files}
    ignored: {ignored_files}''')


    def fix_import(self, file_content: str, import_statement: str) -> (bool, str):
        if (import_statement not in file_content or
                f'{self.new_prefix} {import_statement}' in file_content):
            return False, file_content

        modified_content = file_content.replace(
            import_statement, f"{self.new_prefix} {import_statement}")
        return True, modified_content

    def log_result(self, run_result: RunResult):
        result_processor_name = self.processor_name if self.processor_name is not None else "Processor"
        print(f"{result_processor_name} run result: {run_result}\n")

