#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "BrawlerStage.generated.h"

struct FStageDef;

class UPaperSpriteComponent;

USTRUCT()
struct FStageLayer
{
	GENERATED_BODY()

	UPROPERTY()
	TObjectPtr<UPaperSpriteComponent> Component;

	float BaseX = 0.f;
	float Parallax = 1.f;
	float Z = 0.f;
	float Y = 0.f;
};

/**
 * Baut die Kulisse von Stage 1 aus Sprite-Layern auf:
 * Himmel (Parallax), Fassaden, Boden-Kacheln und Vordergrund-Laternen/Saeulen.
 */
UCLASS()
class STREETSOFBERLIN_API ABrawlerStage : public AActor
{
	GENERATED_BODY()

public:
	ABrawlerStage();

	/** Baut die Kulisse einer Stage (vorherige Layer werden entfernt) */
	void Build(const FStageDef& Def);
	void UpdateParallax(float CameraX);

private:
	void AddLayer(const FString& SpriteName, float BaseX, float CenterZ, float Y, float Parallax, int32 SortPriority);

	UPROPERTY()
	TArray<FStageLayer> Layers;
};
