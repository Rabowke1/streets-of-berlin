#pragma once

#include "CoreMinimal.h"
#include "BrawlerEntity.h"
#include "BrawlerWeaponItem.generated.h"

class ABrawlerFighter;

/** Waffe am Boden (Rohr, Schlaeger, Messer, Flasche, Golfschlaeger). Aufheben mit der Angriffstaste. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerWeaponItem : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerWeaponItem();

	void Init(FName InType, int32 InDurability = -1);
	void Pop(float Direction);
	bool CanCollect() const { return !bCollected && Height <= 0.f; }
	void Collect(ABrawlerFighter* Fighter);
	FName GetWeaponType() const { return Type; }

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	FName Type;
	int32 Durability = -1;
	bool bCollected = false;
	float Life = 0.f;
};

/** Geworfene Waffe: fliegt waagerecht, wirft den ersten getroffenen Gegner um und faellt dann zu Boden. */
UCLASS()
class STREETSOFBERLIN_API ABrawlerProjectile : public ABrawlerEntity
{
	GENERATED_BODY()

public:
	ABrawlerProjectile();

	void Init(FName InType, ABrawlerFighter* InOwner, float InDamage, int32 InDurability);

protected:
	virtual void BeginPlay() override;
	virtual void TickEntity(float DeltaSeconds) override;

	void Land(bool bHit);

	FName Type;
	TWeakObjectPtr<ABrawlerFighter> Thrower;
	EBrawlerTeam Team = EBrawlerTeam::Player;
	float Damage = 12.f;
	int32 Durability = 1;
	float Travel = 0.f;
	float Spin = 0.f;
};
