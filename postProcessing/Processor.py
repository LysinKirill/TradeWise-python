from postProcessing.proto.ExternalClientsRelativePath import ExternalClientsRelativePathProcessor

processors = [
    ExternalClientsRelativePathProcessor(),
]

for processor in processors:
    processor.perform_post_process()
