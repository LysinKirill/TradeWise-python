from postProcessing.proto.ProtoProcessorBase import ProtoProcessorBase


class ExternalClientsRelativePathProcessor(ProtoProcessorBase):
    def __init__(self):
        ProtoProcessorBase.__init__(
            self,
            import_statements_to_replace=[
                "import common_pb2",
                "import users_pb2"
            ],
            files_dir="externalClients/TInvestApi/proto",
            new_prefix="from externalClients.TInvestApi.proto"
        )
        self.processor_name = "ExternalClientsRelativePathProcessor"
