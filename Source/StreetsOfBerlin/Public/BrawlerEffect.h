#pragma once

#include "CoreMinimal.h"
#include "BrawlerEntity.h"
#include "BrawlerEffect.generated.h"

/** Einmal abgespielter Sprite-Effekt (Trefferfunke, Staub, Spezial-Ring). */
UCLASS()
class STREETSOFBERLIN_API ABrawlerEffect : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerEffect();

	void Init(const FString& InPrefix, float InFPS, float InScale, bool bInFront);

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	FString Prefix;
	float FPS = 18.f;
};
