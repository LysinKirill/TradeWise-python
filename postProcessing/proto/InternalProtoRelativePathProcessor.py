from postProcessing.proto.ProtoProcessorBase import ProtoProcessorBase


class InternalProtoRelativePathProcessor(ProtoProcessorBase):
    def __init__(self):
        ProtoProcessorBase.__init__(
            self,
            import_statements_to_replace=[
                "import user_pb2",
                "import invest_pb2"
            ],
            files_dir="app/proto",
            new_prefix="from app.proto"
        )
        self.processor_name = "InternalProtoRelativePathProcessor"
