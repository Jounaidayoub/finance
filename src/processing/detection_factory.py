from src.processing.algos import ZScoreDetectionAlgorithm, SMADetectionAlgorithm

class DetectionAlgorithmFactory:
    @staticmethod
    def get_algorithm(algorithm_type: str):
        if algorithm_type == "z_score":
            return ZScoreDetectionAlgorithm()
        elif algorithm_type == "sma":
            return SMADetectionAlgorithm()
        else:
            raise ValueError(f"Unknown algorithm type: {algorithm_type}")
