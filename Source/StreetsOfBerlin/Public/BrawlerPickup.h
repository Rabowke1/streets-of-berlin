#pragma once

#include "CoreMinimal.h"
#include "BrawlerEntity.h"
#include "BrawlerPickup.generated.h"

class ABrawlerPlayer;

/** Essen (heilt) oder Geld (Punkte). Aufheben mit der Angriffstaste. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerPickup : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerPickup();

	/** Doener, Currywurst oder Money */
	void Init(FName InType);
	bool CanCollect() const { return !bCollected && Height <= 0.f; }
	void Collect(ABrawlerPlayer* Player);

	/** Kleiner Hopser beim Herausfallen aus einer Tonne */
	void Pop(float Direction);

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	FName Type;
	bool bCollected = false;
	float Life = 0.f;
};
