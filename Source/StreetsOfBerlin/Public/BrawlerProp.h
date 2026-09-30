#pragma once

#include "CoreMinimal.h"
#include "BrawlerEntity.h"
#include "BrawlerProp.generated.h"

/** Zerstoerbare Muelltonne / Obstkiste, laesst beim Zerbrechen etwas fallen. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerProp : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerProp();

	/** Type: TrashCan oder Crate; Drop: Doener, Currywurst, Money oder None */
	void Init(FName InType, FName InDrop);

	virtual bool IsHittable(EBrawlerTeam AttackerTeam) const override;
	virtual bool ReceiveHit(ABrawlerFighter* Attacker, const FBrawlerAttack& Attack, float Direction) override;
	virtual float GetHurtHalfWidth() const override { return 38.f; }
	virtual float GetHurtHeight() const override { return 120.f; }

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	FName Type;
	FName Drop;
	int32 HitsLeft = 2;
	bool bBroken = false;
	float BrokenTime = 0.f;
};
