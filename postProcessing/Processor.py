from postProcessing.proto.ExternalClientsRelativePath import ExternalClientsRelativePathProcessor
from postProcessing.proto.InternalProtoRelativePathProcessor import InternalProtoRelativePathProcessor


processors = [
    ExternalClientsRelativePathProcessor(),
    InternalProtoRelativePathProcessor()
]

for processor in processors:
    processor.perform_post_process()
